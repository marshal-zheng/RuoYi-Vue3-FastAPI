import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { compileScript, compileTemplate, parse } from "@vue/compiler-sfc";
import ts from "typescript";
import { describe, expect, it, vi } from "vitest";
import { serializeDateRange } from "@/utils/ruoyi";

const cases = [
  {
    name: "configuration",
    file: "src/views/system/config/components/ConfigList.vue",
    load: "loadConfigData",
    export: "handleExport",
    url: "system/config/export",
    query: { configName: "filtered", configKey: "test.key", configType: "N" },
    dateRange: ["2026-10-01", "2026-10-16"],
  },
  {
    name: "dictionary type",
    file: "src/views/system/dict/components/DictList.vue",
    load: "loadDictData",
    export: "handleExport",
    url: "system/dict/type/export",
    query: { dictName: "filtered", dictType: "test_type", status: "1" },
    dateRange: ["2026-10-01", "2026-10-16"],
  },
  {
    name: "dictionary data",
    file: "src/views/system/dict/data.vue",
    load: "loadDictData",
    export: "handleExport",
    url: "system/dict/data/export",
    query: { dictType: "selected_type", dictLabel: "filtered", status: "1" },
  },
  {
    name: "operation log",
    file: "src/components/business/Monitor/OperlogGrid.vue",
    load: "loadOperlogData",
    export: "exportCurrent",
    url: "monitor/operlog/export",
    query: {
      title: "工程管理",
      operName: "admin",
      businessType: 0,
      status: 0,
      orderByColumn: "operTime",
      isAsc: "descending",
    },
    dateRange: ["2026-10-01 00:00:00", "2026-10-16 23:59:59"],
  },
];

function setup(target: (typeof cases)[number]) {
  const source = readFileSync(resolve(target.file), "utf8");
  const { descriptor } = parse(source);
  const script = compileScript(descriptor, { id: target.name });
  const template = compileTemplate({
    source: descriptor.template!.content,
    filename: target.file,
    id: target.name,
    compilerOptions: { bindingMetadata: script.bindings },
  });
  const ast = ts.createSourceFile(
    "Page.ts",
    descriptor.scriptSetup!.content,
    ts.ScriptTarget.Latest,
  );
  const functions = ast.statements
    .filter(ts.isFunctionDeclaration)
    .map((node) => node.getText(ast));
  const requestViews = ast.statements.filter(ts.isVariableStatement).filter((statement) =>
    statement.declarationList.declarations.some((declaration) =>
      declaration.initializer && ts.isCallExpression(declaration.initializer) &&
      ts.isIdentifier(declaration.initializer.expression) && declaration.initializer.expression.text === "useDictManagementList"
    )
  ).map((node) => node.getText(ast));
  const body = ts.transpileModule([...functions, ...requestViews].join("\n"), {
    compilerOptions: { target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const transform = source.match(
    /<ZxGridList\b[^>]*:query-transform="(\w+)"/,
  )?.[1];
  const snapshot = {
    query: {} as Record<string, unknown>,
    pager: { page: 3, size: 1 },
  };
  const download = vi.fn().mockResolvedValue(undefined);
  const list = vi.fn().mockResolvedValue({ items: [], total: 0 });
  const grid = {
    getStateSnapshot: vi.fn(() => structuredClone(snapshot)),
    updateState(key: string, value: unknown) {
      const [group, field] = key.split(".");
      (snapshot[group as "query" | "pager"] as Record<string, unknown>)[field] =
        value;
    },
    refresh: vi.fn(),
  };
  const dependencies = {
    serializeDateRange,
    useDictManagementList: (load: (params: unknown, options: unknown) => unknown) => ({ loadData: (params: unknown) => load(params, undefined) }),
    listConfig: list,
    listRole: list,
    listType: list,
    listData: list,
    list,
    proxy: { download },
    gridListRef: { value: grid },
    defaultDictType: { value: "obsolete_route_type" },
  };
  const handlers = new Function(
    ...Object.keys(dependencies),
    body +
      `\nreturn { load: ${target.load}, exportData: ${target.export}, transform: ${transform || "(q => q)"},` +
      ' onFilterChange, onSearch, onSortChange: typeof onSortChange === "function" ? onSortChange : undefined };',
  )(...Object.values(dependencies));
  return { snapshot, grid, list, download, handlers, template, source };
}

describe("business list and Excel export filter parity", () => {
  it.each(cases)(
    "$name uses current snapshot filters for list and export, including cleared fields",
    async (target) => {
      const { snapshot, grid, list, download, handlers, template } =
        setup(target);
      expect(template.errors).toEqual([]);
      snapshot.query = {
        ...target.query,
        ...(target.dateRange ? { dateRange: target.dateRange } : {}),
      };
      for (const cleared of [false, true]) {
        if (cleared)
          snapshot.query = target.dateRange ? { dateRange: null } : {};
        const editable = structuredClone(snapshot.query);
        const filters = target.dateRange
          ? serializeDateRange(editable)
          : editable;
        await handlers.load({
          query: handlers.transform(structuredClone(editable)),
          pager: snapshot.pager,
        });
        handlers.exportData();
        expect(list.mock.calls.at(-1)?.[0]).toEqual({
          ...filters,
          page: 3,
          pageSize: 1,
        });
        expect(download).toHaveBeenLastCalledWith(
          target.url,
          filters,
          expect.any(String),
        );
        expect(snapshot.query).toEqual(editable);
      }
      expect(grid.getStateSnapshot).toHaveBeenCalledTimes(2);
    },
  );

  it("operation-log filter and sort events use public GridList state paths and preserve module scope", () => {
    const { snapshot, grid, handlers, source } = setup(cases.find((item) => item.name === "operation log")!);
    snapshot.query = { title: "工程管理", operName: "admin" };
    const actions = {
      updateState: grid.updateState,
      handleRefresh: grid.refresh,
    };
    handlers.onFilterChange("status", 0, actions);
    expect(snapshot.query).toEqual({
      title: "工程管理",
      operName: "admin",
      status: 0,
    });
    expect(snapshot.pager.page).toBe(1);
    snapshot.pager.page = 4;
    handlers.onSortChange({ prop: "costTime", order: "ascending" }, actions);
    expect(snapshot.query).toMatchObject({
      title: "工程管理",
      orderByColumn: "costTime",
      isAsc: "ascending",
    });
    expect(snapshot.pager.page).toBe(1);
    snapshot.pager.page = 4;
    handlers.onSearch(actions);
    expect(snapshot.pager.page).toBe(1);
    expect(grid.refresh).toHaveBeenCalledTimes(3);
    expect(source).not.toContain("getCurrentQuery");
  });
});
