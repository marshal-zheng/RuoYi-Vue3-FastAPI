/**
 * 拓扑图导出工具函数
 * 负责将拓扑图渲染成图片供 Word 导出使用
 */

/* eslint-disable no-console, @typescript-eslint/no-explicit-any, no-undef */
import { Graph } from '@antv/x6';
import { Export } from '@antv/x6-plugin-export';
import { getProjectTopology } from '@/api/project/topology';
import { registerDagShapes, DAG_CONNECTOR } from '@/components/business/Dag/shapes/registerDagShapes';

/**
 * 将 DataURL 转换为 Blob
 */
export function dataURLToBlob(dataURL: string): Blob {
  const arr = dataURL.split(',');
  const mimeMatch = arr[0].match(/:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : 'image/png';
  const bstr = window.atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new window.Blob([u8arr], { type: mime });
}

/**
 * 将 Blob 转换为 Base64 字符串
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new window.FileReader();
    reader.onloadend = () => {
      const result = reader.result as string;
      // 返回纯 base64 字符串（不含 data:xxx;base64, 前缀）
      const base64 = result.split(',')[1] || result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

const sleep = (ms = 16) => new Promise((resolve) => window.setTimeout(resolve, ms));

/**
 * 创建隐藏容器用于离屏渲染
 */
function createHiddenContainer(width = 1200, height = 800): HTMLDivElement {
  const container = window.document.createElement('div');
  Object.assign(container.style, {
    position: 'fixed',
    top: '-10000px',
    left: '-10000px',
    width: `${width}px`,
    height: `${height}px`,
    background: '#ffffff',
    overflow: 'hidden',
    zIndex: '-1',
  });
  window.document.body.appendChild(container);
  return container;
}

/**
 * 等待图实例就绪
 */
async function waitForGraphReady(graph: Graph, timeout = 5000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const nodes = graph.getNodes();
    if (nodes.length > 0) {
      // 确保节点已渲染
      await sleep(300);
      return;
    }
    await sleep(100);
  }
}

interface TopoExportOptions {
  projectId: number;
  versionId?: number;
  width?: number;
  height?: number;
  padding?: number;
  backgroundColor?: string;
}

/**
 * 根据项目和版本ID获取拓扑数据并渲染为图片
 * @returns base64 编码的图片字符串
 */
export async function exportTopologyAsImage(options: TopoExportOptions): Promise<string | null> {
  const {
    projectId,
    versionId,
    width = 1000,
    height = 700,
    padding = 24,
    backgroundColor = '#ffffff',
  } = options;

  let container: HTMLDivElement | null = null;
  let graph: Graph | null = null;

  try {
    // 1. 获取拓扑数据
    const response: any = await getProjectTopology(projectId, versionId);
    const topoData = response?.data?.topologyData;
    const graphJson = topoData?.graph;

    if (!graphJson || !graphJson.cells || graphJson.cells.length === 0) {
      console.warn('拓扑数据为空，跳过图片生成');
      return null;
    }

    // 预注册自定义图形/连线，确保与画布保持一致
    registerDagShapes();

    // 2. 创建离屏容器
    container = createHiddenContainer(width, height);

    // 3. 创建 X6 Graph 实例
    const baseGridOptions = {
      visible: true,
      size: 14,
      type: 'mesh',
      args: {
        color: '#e6e6e6',
        thickness: 1,
      },
    };

    graph = new Graph({
      container,
      width,
      height,
      background: {
        color: backgroundColor,
      },
      grid: baseGridOptions,
      connecting: {
        connector: DAG_CONNECTOR,
      },
      interacting: false,
      async: false,
    });

    // 4. 使用导出插件
    graph.use(new Export());

    // 5. 加载拓扑数据
    graph.fromJSON(graphJson);

    // 6. 等待渲染完成
    await waitForGraphReady(graph);

    // 6.1 强制曲线连接器应用到已有边
    graph.getEdges().forEach((edge) => edge.setConnector(DAG_CONNECTOR));

    // 7. 根据内容自适应画布尺寸（防止截图超大或比例失真）
    try {
      const bbox = graph.getContentBBox();
      const targetWidth = Math.min(Math.max(width, bbox.width + padding * 2), 1400);
      const targetHeight = Math.min(Math.max(height, bbox.height + padding * 2), 1000);
      graph.resize(targetWidth, targetHeight);
      container.style.width = `${targetWidth}px`;
      container.style.height = `${targetHeight}px`;
      graph.zoomToFit({
        padding: { top: padding, right: padding, bottom: padding, left: padding },
        minScale: 0.2,
        maxScale: 1.0,
      });
      graph.centerContent();
    } catch (error) {
      console.warn('调整图布局失败:', error);
    }

    // 再等待一下确保布局调整完成
    await sleep(200);

    // 8. 导出为 PNG DataURL
    const dataURL = await new Promise<string>((resolve, reject) => {
      try {
        graph!.toPNG(
          (dataUri: string) => {
            resolve(dataUri);
          },
          {
            backgroundColor,
            padding,
            quality: 1,
            copyStyles: true,
            preserveDimensions: true,
          } as any
        );
      } catch (error) {
        reject(error);
      }
    });

    // 9. 转换为 base64
    const blob = dataURLToBlob(dataURL);
    const base64 = await blobToBase64(blob);

    return base64;
  } catch (error) {
    console.error('导出拓扑图失败:', error);
    return null;
  } finally {
    // 清理资源
    if (graph) {
      try {
        graph.dispose();
      } catch {
        // ignore
      }
    }
    if (container) {
      container.remove();
    }
  }
}

/**
 * 直接从 graph JSON 数据导出图片（不需要调用 API）
 */
export async function exportGraphJsonAsImage(
  graphJson: any,
  options: Omit<TopoExportOptions, 'projectId' | 'versionId'> = {}
): Promise<string | null> {
  const { width = 1200, height = 800, padding = 40, backgroundColor = '#ffffff' } = options;

  if (!graphJson || !graphJson.cells || graphJson.cells.length === 0) {
    console.warn('拓扑数据为空，跳过图片生成');
    return null;
  }

  let container: HTMLDivElement | null = null;
  let graph: Graph | null = null;

  try {
    // 创建离屏容器
    container = createHiddenContainer(width, height);

    registerDagShapes();

    // 创建 X6 Graph 实例
    graph = new Graph({
      container,
      width,
      height,
      background: {
        color: backgroundColor,
      },
      grid: {
        visible: true,
        size: 14,
        type: 'mesh',
        args: {
          color: '#e6e6e6',
          thickness: 1,
        },
      },
      interacting: false,
      async: false,
    });

    // 使用导出插件
    graph.use(new Export());

    // 加载拓扑数据
    graph.fromJSON(graphJson);

    // 等待渲染完成
    await waitForGraphReady(graph);

    // 自动适应画布
    try {
      graph.zoomToFit({
        padding: { top: padding, right: padding, bottom: padding, left: padding },
        minScale: 0.3,
        maxScale: 1.5,
      });
      graph.centerContent();
    } catch (error) {
      console.warn('调整图布局失败:', error);
    }

    await sleep(200);

    // 导出为 PNG DataURL
    const dataURL = await new Promise<string>((resolve, reject) => {
      try {
        graph!.toPNG(
          (dataUri: string) => {
            resolve(dataUri);
          },
          {
            backgroundColor,
            padding,
            quality: 1,
            copyStyles: true,
            preserveDimensions: true,
          } as any
        );
      } catch (error) {
        reject(error);
      }
    });

    // 转换为 base64
    const blob = dataURLToBlob(dataURL);
    const base64 = await blobToBase64(blob);

    return base64;
  } catch (error) {
    console.error('导出拓扑图失败:', error);
    return null;
  } finally {
    if (graph) {
      try {
        graph.dispose();
      } catch {
        // ignore
      }
    }
    if (container) {
      container.remove();
    }
  }
}
