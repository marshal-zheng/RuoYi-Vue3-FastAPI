import { parse } from '@vue/compiler-sfc';
import ts from 'typescript';
import postcss from 'postcss';
import path from 'node:path';

const PRESETS = new Set(['sm', 'md', 'lg', 'xl', 'small', 'large']);
const CORE_THEME_VARIABLE = /^--(?:el|zx)-/;
const normalizeTag = (tag) => tag.replace(/-/g, '').toLowerCase();
const propName = (node) => node?.name?.text ?? node?.name?.escapedText;
const unparen = (node) => {
  while (
    node &&
    (ts.isParenthesizedExpression(node) ||
      ts.isAsExpression(node) ||
      ts.isSatisfiesExpression(node))
  )
    node = node.expression;
  return node;
};

function checker(source, filePath) {
  const violations = [];
  return {
    violations,
    add(rule, message, offset = 0) {
      const prefix = source.slice(0, Math.max(offset, 0));
      const lines = prefix.split('\n');
      violations.push({
        rule,
        message,
        file: filePath,
        line: lines.length,
        column: lines.at(-1).length + 1,
      });
    },
  };
}

const QUERY_CACHE_COMMANDS = new Set([
  'invalidateQueries',
  'cancelQueries',
  'removeQueries',
  'resetQueries',
  'setQueryData',
  'setQueriesData',
  'clear',
]);
const QUERY_KEY_ARGUMENTS = new Set([
  'getQueryData',
  'getQueryState',
  'setQueryData',
  'getQueryDefaults',
  'setQueryDefaults',
]);
const QUERY_WRAPPERS = new Set([
  'ref',
  'shallowRef',
  'reactive',
  'shallowReactive',
  'computed',
  'unref',
  'toValue',
]);
const QUERY_RESOURCE_POLICY =
  /^(?:queryKey|queryFn|queryHash|queryKeyHashFn|enabled|staleTime|gcTime|retry.*|refetch.*|networkMode|initialData.*|placeholderData|persister|structuralSharing)$/;

/** Import provenance and local expressions only; public query modules own their exports. */
function analyzeQuerySources(ast, ctx, offset, filePath) {
  const normalizedFile = filePath.replaceAll('\\', '/');
  const isQueryModule = (module) => /(?:^|\/)src\/queries(?:\/|$)/.test(module);
  if (isQueryModule(normalizedFile)) return;
  const isConsumer = /(?:^|\/)src\/(?:views|components)\//.test(normalizedFile);
  const modulePath = (source) =>
    source.startsWith('@/')
      ? `src/${source.slice(2)}`
      : source.startsWith('.')
        ? path.posix.normalize(path.posix.join(path.posix.dirname(normalizedFile), source))
        : source;
  const scopes = new WeakMap();
  const root = { parent: null, bindings: new Map() };
  function bindName(name, scope, value, type) {
    if (ts.isIdentifier(name)) scope.bindings.set(name.text, { value, type });
    else if (ts.isObjectBindingPattern(name)) {
      for (const entry of name.elements)
        if (ts.isIdentifier(entry.name))
          scope.bindings.set(entry.name.text, {
            value,
            member: entry.propertyName?.text ?? entry.name.text,
          });
    }
  }
  function index(node, scope) {
    if (ts.isFunctionDeclaration(node) && node.name)
      scope.bindings.set(node.name.text, { value: node });
    if (ts.isFunctionLike(node) || ts.isBlock(node)) scope = { parent: scope, bindings: new Map() };
    scopes.set(node, scope);
    if (ts.isVariableDeclaration(node) || ts.isParameter(node))
      bindName(node.name, scope, node.initializer, node.type);
    if (
      ts.isImportDeclaration(node) &&
      node.importClause &&
      ts.isStringLiteral(node.moduleSpecifier)
    ) {
      const module = modulePath(node.moduleSpecifier.text);
      const clause = node.importClause;
      if (clause.name) scope.bindings.set(clause.name.text, { module, name: 'default' });
      const named = clause.namedBindings;
      if (named && ts.isNamespaceImport(named))
        scope.bindings.set(named.name.text, { module, name: '' });
      else if (named)
        for (const entry of named.elements)
          scope.bindings.set(entry.name.text, {
            module,
            name: entry.propertyName?.text ?? entry.name.text,
          });
    }
    ts.forEachChild(node, (child) => index(child, scope));
  }
  index(ast, root);
  function binding(node) {
    for (let scope = scopes.get(node); scope; scope = scope.parent) {
      const found = scope.bindings.get(node.text);
      if (found) return found;
    }
    return undefined;
  }
  function origin(node, seen = new Set()) {
    node = unparen(node);
    if (!node || seen.has(node)) return null;
    seen = new Set([...seen, node]);
    if (ts.isIdentifier(node)) {
      const found = binding(node);
      if (found?.module) return found;
      if (found?.member && isClient(found.value))
        return { module: 'QueryClient', name: found.member };
      return found?.value ? origin(found.value, seen) : null;
    }
    if (ts.isPropertyAccessExpression(node) || ts.isQualifiedName(node)) {
      if (ts.isPropertyAccessExpression(node) && isClient(node.expression))
        return { module: 'QueryClient', name: node.name.text };
      const parent = origin(node.expression ?? node.left, seen);
      const name = (node.name ?? node.right).text;
      if (parent)
        return {
          module: parent.module,
          name: [parent.name, name].filter(Boolean).join('.'),
        };
    }
    return null;
  }
  const isTanStack = (source, name) =>
    source?.module === '@tanstack/vue-query' && source.name === name;
  const isImportedClient = (source) =>
    source &&
    /(?:^|\/)src\/queries\/client(?:\.[cm]?[jt]s)?$/.test(source.module) &&
    ['queryClient', 'default'].includes(source.name);
  function isClient(node, seen = new Set()) {
    node = unparen(node);
    if (!node || seen.has(node)) return false;
    seen = new Set([...seen, node]);
    if (ts.isIdentifier(node)) {
      const found = binding(node);
      if (found?.module) return isImportedClient(found);
      if (
        found?.type &&
        ts.isTypeReferenceNode(found.type) &&
        isTanStack(origin(found.type.typeName), 'QueryClient')
      )
        return true;
      return found?.value ? isClient(found.value, seen) : false;
    }
    if (ts.isPropertyAccessExpression(node)) return isImportedClient(origin(node));
    if (ts.isNewExpression(node)) return isTanStack(origin(node.expression), 'QueryClient');
    return ts.isCallExpression(node) && isTanStack(origin(node.expression), 'useQueryClient');
  }
  function returns(node) {
    if (!node.body) return [];
    if (!ts.isBlock(node.body)) return node.body ? [node.body] : [];
    const values = [];
    const walk = (child) => {
      if (ts.isReturnStatement(child)) {
        values.push(child.expression);
        return;
      }
      if (!ts.isFunctionLike(child)) ts.forEachChild(child, walk);
    };
    ts.forEachChild(node.body, walk);
    return values;
  }
  function wrapper(node) {
    if (!ts.isCallExpression(node)) return false;
    const imported = origin(node.expression);
    return (
      (imported?.module === 'vue' && QUERY_WRAPPERS.has(imported.name)) ||
      (ts.isIdentifier(node.expression) &&
        !binding(node.expression) &&
        QUERY_WRAPPERS.has(node.expression.text))
    );
  }
  // Follow reactive containers/getters without evaluating or dereferencing their parameters.
  function follow(node, inspect, seen = new Set()) {
    node = unparen(node);
    if (!node || seen.has(node)) return false;
    seen = new Set([...seen, node]);
    if (ts.isIdentifier(node)) {
      const found = binding(node);
      if (found?.value && !found.member) return follow(found.value, inspect, seen);
    }
    if (
      ts.isArrowFunction(node) ||
      ts.isFunctionExpression(node) ||
      ts.isFunctionDeclaration(node)
    ) {
      const values = returns(node);
      return values.length > 0 && values.every((value) => follow(value, inspect, seen));
    }
    if (ts.isPropertyAccessExpression(node) && node.name.text === 'value')
      return follow(node.expression, inspect, seen);
    if (wrapper(node)) return follow(node.arguments[0], inspect, seen);
    if (ts.isConditionalExpression(node))
      return follow(node.whenTrue, inspect, seen) && follow(node.whenFalse, inspect, seen);
    return inspect(node, seen);
  }
  const isFactory = (node) => isQueryModule(origin(node)?.module ?? '');
  function optionsFromFactory(node, seen) {
    return follow(
      node,
      (value, visited) => {
        if (ts.isCallExpression(value)) return isFactory(value.expression);
        if (!ts.isObjectLiteralExpression(value)) return false;
        let factory = false;
        for (const entry of value.properties) {
          if (ts.isSpreadAssignment(entry)) {
            if (!optionsFromFactory(entry.expression, visited)) return false;
            factory = true;
          } else if (
            ts.isComputedPropertyName(entry.name) ||
            QUERY_RESOURCE_POLICY.test(String(propName(entry)))
          )
            return false;
        }
        return factory;
      },
      seen
    );
  }
  function queryArrayFromFactory(node, seen) {
    return follow(
      node,
      (value, visited) => {
        if (ts.isArrayLiteralExpression(value))
          return value.elements.every((item) =>
            ts.isSpreadElement(item)
              ? queryArrayFromFactory(item.expression, visited)
              : optionsFromFactory(item, visited)
          );
        if (ts.isCallExpression(value)) {
          if (isFactory(value.expression)) return true;
          if (
            ts.isPropertyAccessExpression(value.expression) &&
            value.expression.name.text === 'map'
          ) {
            const callback = value.arguments[0];
            return isFactory(callback) || optionsFromFactory(callback, visited);
          }
        }
        return false;
      },
      seen
    );
  }
  function multipleFromFactory(node) {
    return follow(node, (value, visited) => {
      if (!ts.isObjectLiteralExpression(value)) return false;
      const queries = value.properties.find((entry) => propName(entry) === 'queries');
      return (
        queries &&
        queryArrayFromFactory(
          ts.isShorthandPropertyAssignment(queries) ? queries.name : queries.initializer,
          visited
        )
      );
    });
  }
  const reportedKeys = new Set();
  function literalKey(node) {
    follow(node, (value) => {
      if (ts.isArrayLiteralExpression(value) && !reportedKeys.has(value)) {
        reportedKeys.add(value);
        ctx.add(
          'query-key-definition',
          '查询 key 数组须集中在 src/queries，由公共查询工厂导出。',
          offset + value.getStart(ast)
        );
      }
      return true;
    });
  }
  function inspectKeys(node, seen) {
    follow(
      node,
      (value, visited) => {
        if (ts.isObjectLiteralExpression(value)) {
          for (const entry of value.properties) {
            if (ts.isSpreadAssignment(entry)) inspectKeys(entry.expression, visited);
            else {
              const expression = ts.isShorthandPropertyAssignment(entry)
                ? entry.name
                : entry.initializer;
              if (propName(entry) === 'queryKey') literalKey(expression);
              if (propName(entry) === 'queries') inspectKeys(expression, visited);
            }
          }
        } else if (ts.isArrayLiteralExpression(value))
          for (const entry of value.elements) inspectKeys(entry, visited);
        else if (
          ts.isCallExpression(value) &&
          ts.isPropertyAccessExpression(value.expression) &&
          value.expression.name.text === 'map'
        )
          inspectKeys(value.arguments[0], visited);
        return true;
      },
      seen
    );
  }
  function inspect(node) {
    if (ts.isCallExpression(node)) {
      const imported = origin(node.expression);
      const nativeQuery = isTanStack(imported, 'useQuery');
      const multiple = isTanStack(imported, 'useQueries');
      const select =
        imported?.module === '@zxio/vue-query/ui' && imported.name === 'useQuerySelect';
      if (nativeQuery || multiple || select || isTanStack(imported, 'queryOptions')) {
        inspectKeys(node.arguments[0]);
        if (
          isConsumer &&
          (nativeQuery || multiple || select) &&
          !(multiple
            ? multipleFromFactory(node.arguments[0])
            : optionsFromFactory(node.arguments[0]))
        )
          ctx.add(
            'query-options-source',
            '查询 options 须来自 src/queries 公共工厂；允许本地 ref/computed/getter 与工厂数组/map，不在页面覆盖资源策略。动态来源无法局部解析时请改用可识别的工厂引用。',
            offset + node.getStart(ast)
          );
      }
      if (imported?.module === 'QueryClient') {
        if (QUERY_CACHE_COMMANDS.has(imported.name))
          ctx.add(
            'query-cache-command',
            '原生缓存修改须集中在 src/queries 公共命令或会话入口。',
            offset + node.getStart(ast)
          );
        if (QUERY_KEY_ARGUMENTS.has(imported.name)) literalKey(node.arguments[0]);
        else inspectKeys(node.arguments[0]);
      }
    }
    ts.forEachChild(node, inspect);
  }
  inspect(ast);
}

/** Narrow local analysis: literal options/constants and the mandated form entry. */
function analyzeScript(text, ctx, offset = 0, filePath = '') {
  const ast = ts.createSourceFile(
    filePath || 'component.ts',
    text,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX
  );
  analyzeQuerySources(ast, ctx, offset, filePath);
  const locals = new Map();
  const hooks = new Map([
    ['useDialog', 'dialog'],
    ['useFormDialog', 'form'],
  ]);
  const bindings = new Map();
  const calls = [];
  const visit = (node) => {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer)
      locals.set(node.name.text, node.initializer);
    if (
      ts.isImportDeclaration(node) &&
      node.importClause?.namedBindings &&
      ts.isNamedImports(node.importClause.namedBindings)
    ) {
      for (const element of node.importClause.namedBindings.elements) {
        const original = element.propertyName?.text ?? element.name.text;
        if (original === 'useDialog' || original === 'useFormDialog')
          hooks.set(element.name.text, original === 'useDialog' ? 'dialog' : 'form');
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(ast);
  function resolve(node, seen = new Set()) {
    node = unparen(node);
    if (!node) return null;
    if (ts.isIdentifier(node) && locals.has(node.text) && !seen.has(node.text)) {
      return resolve(locals.get(node.text), new Set([...seen, node.text]));
    }
    if (
      ts.isCallExpression(node) &&
      ts.isIdentifier(node.expression) &&
      ['ref', 'reactive', 'shallowReactive', 'computed', 'unref'].includes(node.expression.text)
    ) {
      let argument = node.arguments[0];
      if (argument && ts.isArrowFunction(argument))
        argument = ts.isBlock(argument.body)
          ? argument.body.statements.find(ts.isReturnStatement)?.expression
          : argument.body;
      return resolve(argument, seen);
    }
    return node;
  }
  function literal(node) {
    const resolved = resolve(node);
    if (resolved && (ts.isStringLiteralLike(resolved) || ts.isNumericLiteral(resolved)))
      return resolved.text;
    return null;
  }
  function object(node) {
    const resolved = resolve(node);
    return resolved && ts.isObjectLiteralExpression(resolved) ? resolved : null;
  }
  function properties(node) {
    const value = object(node);
    if (!value) return null;
    if (
      value.properties.some(
        (entry) =>
          ts.isSpreadAssignment(entry) || (entry.name && ts.isComputedPropertyName(entry.name))
      )
    )
      return null;
    return new Map(
      value.properties.map((entry) => [
        String(propName(entry)),
        ts.isShorthandPropertyAssignment(entry) ? entry.name : entry.initializer,
      ])
    );
  }
  function validateDialogOptions(node, kind, at) {
    const props = properties(node);
    if (!props) {
      ctx.add(
        'dialog-options-unresolved',
        '弹框配置须使用可解析本地对象或 useFormDialog 统一入口，不支持未知 spread/间接配置。',
        at
      );
      return;
    }
    if (props.has('width') || props.has('height'))
      ctx.add('dialog-dimensions', '弹框使用 dialogSize 预设；不得直接配置 width/height。', at);
    if (props.has('maxHeight'))
      ctx.add('dialog-max-height', '最大高度写入 dialogStyle.maxHeight，顶层 maxHeight 无效。', at);
    if (props.has('dialogStyle')) {
      const style = properties(props.get('dialogStyle'));
      if (!style)
        ctx.add(
          'dialog-style-unresolved',
          'dialogStyle 须为可解析本地对象，只允许内容限高等样式。',
          at
        );
      else if (style.has('width') || style.has('height'))
        ctx.add('dialog-dimensions', 'dialogStyle 不得绕过预设尺寸或内容高度。', at);
    }
    if (kind === 'form') {
      const columns = literal(props.get('columns'));
      if (!['1', '2', '3'].includes(columns))
        ctx.add('form-columns', 'useFormDialog 须显式提供可解析的 columns: 1 | 2 | 3。', at);
      if (props.has('dialogSize') && !PRESETS.has(literal(props.get('dialogSize'))))
        ctx.add('dialog-preset', 'dialogSize 覆盖必须是合法预设。', at);
    } else {
      if (!PRESETS.has(literal(props.get('dialogSize'))))
        ctx.add('dialog-preset', '非表单弹框须显式提供合法 dialogSize 预设。', at);
      if (props.has('formRef'))
        ctx.add(
          'form-dialog-entry',
          '表单弹框使用 useFormDialog 提供同源 dialogProps/formProps/layoutProps。',
          at
        );
    }
  }
  const inspect = (node) => {
    const at = offset + node.getStart(ast);
    if (
      (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) &&
      node.moduleSpecifier &&
      ts.isStringLiteral(node.moduleSpecifier)
    ) {
      if (
        /(@zxio\/theme-[^/]+\/(?:generated|src)\/|compiled-zxui|node_modules\/@zxio\/theme-)/.test(
          node.moduleSpecifier.text
        )
      )
        ctx.add('private-theme-path', '浏览器只能消费公开主题导出与部署 resolver。', at);
    }
    if (
      ts.isModuleDeclaration(node) &&
      ts.isStringLiteral(node.name) &&
      node.name.text.startsWith('@zxio/')
    )
      ctx.add('public-type-patch', '公开类型缺口在 ZXUI 修复，业务不得补写模块声明。', at);
    if (ts.isPropertyAssignment(node) && CORE_THEME_VARIABLE.test(String(propName(node))))
      ctx.add('competing-theme-write', '业务不得写入核心 --el-* / --zx-* 主题值。', at);
    if (ts.isCallExpression(node)) {
      if (
        ts.isPropertyAccessExpression(node.expression) &&
        node.expression.name.text === 'setProperty' &&
        CORE_THEME_VARIABLE.test(literal(node.arguments[0]) || '')
      )
        ctx.add('competing-theme-write', '业务不得通过 style.setProperty 写入核心主题值。', at);
      if (
        node.expression.getText(ast) === 'import.meta.glob' &&
        node.arguments.some((arg) =>
          /(?:theme-|compiled-zxui).*(?:generated|compiled-zxui)|compiled-zxui/.test(
            arg.getText(ast)
          )
        )
      )
        ctx.add('private-theme-path', '浏览器不得遍历主题 generated 目录。', at);
      if (ts.isIdentifier(node.expression) && hooks.has(node.expression.text)) {
        const kind = hooks.get(node.expression.text);
        // The entry implementation owns dynamic sanitizing and type/runtime checks.
        if (!filePath.replaceAll('\\', '/').endsWith('src/components/ui/FormDialog/index.ts'))
          validateDialogOptions(node.arguments[0], kind, at);
        const owner = `${at}`;
        let declaration = node.parent;
        while (
          declaration &&
          !ts.isVariableDeclaration(declaration) &&
          !ts.isStatement(declaration)
        )
          declaration = declaration.parent;
        if (declaration && ts.isVariableDeclaration(declaration)) {
          if (ts.isIdentifier(declaration.name)) {
            for (const key of ['dialogProps', 'formProps', 'layoutProps'])
              bindings.set(`${declaration.name.text}.${key}`, { kind, key, owner });
          } else if (ts.isObjectBindingPattern(declaration.name)) {
            for (const entry of declaration.name.elements) {
              const key = entry.propertyName?.text ?? entry.name.text;
              if (
                ['dialogProps', 'formProps', 'layoutProps'].includes(key) &&
                ts.isIdentifier(entry.name)
              )
                bindings.set(entry.name.text, { kind, key, owner });
            }
          }
        }
        calls.push({ kind, at });
      }
    }
    ts.forEachChild(node, inspect);
  };
  inspect(ast);
  // A controller may be destructured once locally; no cross-file data-flow is needed.
  const bindLocalDestructuring = (node) => {
    if (
      ts.isVariableDeclaration(node) &&
      ts.isObjectBindingPattern(node.name) &&
      node.initializer
    ) {
      const controller = node.initializer.getText(ast).replace(/\.value$/, '');
      for (const entry of node.name.elements) {
        const key = entry.propertyName?.text ?? entry.name.text;
        const existing = bindings.get(`${controller}.${key}`);
        if (existing && ts.isIdentifier(entry.name)) bindings.set(entry.name.text, existing);
      }
    }
    ts.forEachChild(node, bindLocalDestructuring);
  };
  bindLocalDestructuring(ast);
  return { bindings, calls, properties, literal, resolve, validateDialogOptions };
}

function checkStyles(text, ctx, offset = 0) {
  // PostCSS handles ordinary CSS and the declaration blocks used in our Less styles.
  try {
    const ast = postcss.parse(text);
    ast.walkDecls((decl) => {
      if (
        ['width', 'height'].includes(decl.prop) &&
        /\.(?:el|zx)-dialog(?:\s*[,>{:]|$)/.test(decl.parent?.selector || '') &&
        decl.value !== 'auto'
      )
        ctx.add(
          'dialog-css-dimensions',
          '弹框 CSS 不得直接覆盖 width/height；在调用点使用预设与 dialogStyle.maxHeight。',
          offset + (decl.source?.start?.offset ?? 0)
        );
      if (CORE_THEME_VARIABLE.test(decl.prop))
        ctx.add(
          'competing-theme-write',
          '业务样式不得声明核心 --el-* / --zx-* 主题值。',
          offset + (decl.source?.start?.offset ?? 0)
        );
    });
  } catch {
    // Less interpolation may not be valid CSS. Limit fallback to actual declaration lines.
    const stripped = text.replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/[^\n]/g, ' '));
    for (const match of stripped.matchAll(/(?:^|[;{\n])\s*(--(?:el|zx)-[\w-]+)\s*:/g))
      ctx.add('competing-theme-write', '业务样式不得声明核心主题值。', offset + match.index);
  }
}

/** Shared by repository scanning and generated SFC tests. No baseline or per-page waiver. */
export function checkVueSource(source, { filePath = 'generated.vue', checkRawInput = true } = {}) {
  const ctx = checker(source, filePath);
  const { descriptor, errors } = parse(source, { filename: filePath });
  for (const error of errors)
    ctx.add(
      'vue-parse',
      typeof error === 'string' ? error : error.message,
      error.loc?.start?.offset ?? 0
    );
  const scripts = [descriptor.script, descriptor.scriptSetup].filter(Boolean);
  const analyses = scripts.map((script) =>
    analyzeScript(script.content, ctx, script.loc.start.offset, filePath)
  );
  const bindings = new Map(analyses.flatMap((analysis) => [...analysis.bindings]));
  const analysis = analyses.at(-1);
  const templateOffset = descriptor.template?.loc.start.offset ?? 0;
  const at = (node) => templateOffset + node.loc.start.offset;
  const expression = (text) =>
    ts.createSourceFile('expr.ts', `(${text})`, ts.ScriptTarget.Latest, true).statements[0]
      ?.expression;
  const binding = (value) => bindings.get(value?.replace(/\.value$/, ''));
  const prop = (node, key) =>
    node.props.find((entry) =>
      entry.type === 6 ? entry.name === key : entry.name === 'bind' && entry.arg?.content === key
    );
  const spread = (node) =>
    node.props.filter((entry) => entry.type === 7 && entry.name === 'bind' && !entry.arg);
  const value = (entry) => (entry?.type === 6 ? entry.value?.content : entry?.exp?.content);
  const descendant = (node, tag) =>
    (node.children || []).some(
      (child) => child.type === 1 && (normalizeTag(child.tag) === tag || descendant(child, tag))
    );
  const walk = (node, parentDialog = null, parentForm = null, parentInput = false) => {
    if (node.type !== 1) {
      for (const child of node.children || []) walk(child, parentDialog, parentForm, parentInput);
      return;
    }
    const tag = normalizeTag(node.tag);
    const input = parentInput || tag === 'zxinput' || tag === 'elinput';
    if (
      parentInput &&
      node.props.some((entry) => entry.type === 6 && ['slot', 'slot-scope'].includes(entry.name))
    )
      ctx.add(
        'legacy-input-slot',
        '输入插槽使用 Vue 3 template #prefix/#suffix/#prepend/#append 语法。',
        at(node)
      );
    for (const attribute of node.props) {
      if (
        attribute.type === 6 &&
        attribute.name === 'style' &&
        /--(?:el|zx)-[\w-]+\s*:/.test(attribute.value?.content || '')
      )
        ctx.add('competing-theme-write', '模板不得写入核心主题值。', at(attribute));
      if (attribute.type === 7 && attribute.name === 'bind' && attribute.arg?.content === 'style') {
        const entries = analysis?.properties(expression(value(attribute)));
        if (entries && [...entries.keys()].some((key) => CORE_THEME_VARIABLE.test(key)))
          ctx.add('competing-theme-write', '模板不得写入核心主题值。', at(attribute));
      }
    }
    let dialog = parentDialog;
    let form = parentForm;
    if (tag === 'eldialog') ctx.add('no-raw-el-dialog', '范围内弹框统一使用 ZxDialog。', at(node));
    if (checkRawInput && tag === 'elinput')
      ctx.add(
        'no-raw-el-input',
        '范围内原生输入统一使用 ZxInput；el-input-number 不受此规则影响。',
        at(node)
      );
    if (tag === 'zxdialog' || tag === 'eldialog') {
      dialog = { node, owner: undefined };
      form = null;
      for (const key of ['width', 'height', 'max-height', 'maxHeight'])
        if (prop(node, key))
          ctx.add(
            'dialog-dimensions',
            '弹框尺寸使用预设，限高使用 dialogStyle.maxHeight。',
            at(prop(node, key))
          );
      const size = prop(node, 'dialog-size') || prop(node, 'dialogSize');
      let hasSize =
        size?.type === 6
          ? PRESETS.has(value(size))
          : size && PRESETS.has(analysis?.literal(expression(value(size))));
      for (const item of spread(node)) {
        const known = binding(value(item));
        if (known?.key === 'dialogProps') {
          hasSize = true;
          if (known.kind === 'form') dialog.owner = known.owner;
        } else if (analysis) {
          const options = expression(value(item));
          analysis.validateDialogOptions(
            options,
            descendant(node, 'elform') ? 'form' : 'dialog',
            at(item)
          );
          hasSize = Boolean(analysis.properties(options));
        } else
          ctx.add(
            'dialog-options-unresolved',
            '弹框 v-bind 必须来自本地可解析配置或统一入口。',
            at(item)
          );
      }
      if (!hasSize)
        ctx.add('dialog-preset', '弹框必须显式选预设或绑定统一入口的 dialogProps。', at(node));
      for (const key of ['style', 'dialog-style', 'dialogStyle']) {
        const style = prop(node, key);
        if (!style) continue;
        if (style.type === 6) {
          if (/(?:^|;)\s*(?:width|height)\s*:/.test(value(style) || ''))
            ctx.add('dialog-dimensions', 'style 不能绕过弹框预设尺寸和内容高度。', at(style));
        } else {
          const entries = analysis?.properties(expression(value(style)));
          if (!entries)
            ctx.add(
              'dialog-style-unresolved',
              '动态弹框样式须收敛到受约束的 dialogStyle 本地对象。',
              at(style)
            );
          else if (entries.has('width') || entries.has('height'))
            ctx.add('dialog-dimensions', 'style 不能绕过弹框预设尺寸和内容高度。', at(style));
        }
      }
    }
    if (
      dialog &&
      tag === 'elform' &&
      !['true', ''].includes(value(prop(node, 'inline')) ?? 'false')
    ) {
      const formBinding = spread(node)
        .map((item) => binding(value(item)))
        .find((entry) => entry?.key === 'formProps' && entry.kind === 'form');
      form = { node, owner: formBinding?.owner };
      if (!formBinding)
        ctx.add(
          'form-layout-entry',
          '弹框 ElForm 须绑定 useFormDialog 返回的 formProps。',
          at(node)
        );
      else if (!dialog.owner || dialog.owner !== formBinding.owner)
        ctx.add(
          'form-dialog-source',
          '弹框的 dialogProps 与 ElForm 的 formProps 必须来自同一个 useFormDialog。',
          at(node)
        );
      if (!descendant(node, 'formgrid'))
        ctx.add('form-grid', '弹框表单字段通过 FormGrid 使用统一布局策略。', at(node));
    }
    if (dialog && form) {
      if (['elform', 'elformitem'].includes(tag) && prop(node, 'label-width'))
        ctx.add(
          'form-label-width',
          '标签宽度由 formProps 统一下发，调用点不另写 label-width。',
          at(prop(node, 'label-width'))
        );
      if (tag === 'elcol' && prop(node, 'span'))
        ctx.add('form-field-span', '字段用 data-form-full 表达整行，不写 span 几何值。', at(node));
      if (tag === 'elrow' && prop(node, 'gutter'))
        ctx.add('form-field-gap', '字段横向间距由 FormGrid 策略管理。', at(node));
      if (tag === 'formgrid') {
        const gridBinding = spread(node)
          .map((item) => binding(value(item)))
          .find((entry) => entry?.key === 'layoutProps' && entry.kind === 'form');
        if (
          !gridBinding ||
          !form.owner ||
          gridBinding.owner !== form.owner ||
          prop(node, 'columns')
        )
          ctx.add(
            'form-layout-source',
            'FormGrid 的 layoutProps 必须与 ElForm 的 formProps 来自同一个 useFormDialog。',
            at(node)
          );
        if (prop(node, 'style'))
          ctx.add('form-field-gap', 'FormGrid 不接受调用点布局样式覆盖。', at(node));
      }
    }
    for (const child of node.children || []) walk(child, dialog, form, input);
  };
  if (descriptor.template?.src)
    ctx.add(
      'external-template',
      '模板必须可静态检查，不能引用未知外部 template src。',
      descriptor.template.loc.start.offset
    );
  if (descriptor.template?.ast) walk(descriptor.template.ast);
  for (const style of descriptor.styles) checkStyles(style.content, ctx, style.loc.start.offset);
  return ctx.violations;
}

export function checkSource(source, { filePath, checkRawInput = true }) {
  if (filePath.endsWith('.vue')) return checkVueSource(source, { filePath, checkRawInput });
  const ctx = checker(source, filePath);
  if (/\.(?:css|less|scss)$/.test(filePath)) checkStyles(source, ctx);
  else analyzeScript(source, ctx, 0, filePath);
  return ctx.violations;
}

export const UI_SCOPE = Object.freeze({
  include: 'src/**/*.{vue,ts,tsx,js,jsx,css,less,scss}',
  excludedModules: [
    'src/views/project/simulation/**',
    'src/views/project/components/SimulationResultDialog.vue',
    'src/views/project/components/SimulationStatusPanel.vue',
  ],
  explanation:
    '仿真目录及已确认仿真专用组件不在规格范围；所有非仿真共享消费者均检查。测试/声明文件不作为页面实例，公开类型补丁仍检查。',
});
