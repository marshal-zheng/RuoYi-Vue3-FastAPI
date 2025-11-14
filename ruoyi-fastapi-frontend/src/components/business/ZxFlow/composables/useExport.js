import { Export } from '@antv/x6-plugin-export'
import { useGraphInstance } from './useGraphInstance'

let CachedJsPDF = null

const ensureJsPDF = async () => {
  if (CachedJsPDF) return CachedJsPDF
  const mod = await import('jspdf')
  CachedJsPDF = mod?.default || mod?.jsPDF || mod
  return CachedJsPDF
}

const isRefLike = (maybeRef) =>
  Boolean(maybeRef && typeof maybeRef === 'object' && 'value' in maybeRef)

const downloadBlob = (content, fileName, mimeType) => {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

const loadImage = (src) =>
  new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })

export function useExport(graphInstance = null) {
  let graph

  try {
    graph = graphInstance || useGraphInstance()
  } catch (error) {
    graph = graphInstance
  }

  const getGraph = () => {
    if (!graph) return null
    return isRefLike(graph) ? graph.value : graph
  }

  const ensureGraph = () => {
    const g = getGraph()
    if (!g) {
      throw new Error(
        'Graph instance is not available – make sure the graph has been initialised before exporting.'
      )
    }
    return g
  }

  const ensureExportPlugin = (g) => {
    if (!g) return null
    const existing = typeof g.getPlugin === 'function' ? g.getPlugin('export') : null
    if (existing) return existing
    const instance = new Export()
    if (typeof g.use === 'function') {
      g.use(instance)
    }
    return instance
  }

  const getElementChildren = (element) =>
    Array.from(element?.childNodes || []).filter((node) => node.nodeType === 1)

  const inlineComputedStyle = (sourceEl, targetEl) => {
    if (!sourceEl || !targetEl) return
    const win = sourceEl.ownerDocument?.defaultView
    if (!win) return

    try {
      const computed = win.getComputedStyle(sourceEl)
      const styleText = Array.from(computed)
        .map((prop) => `${prop}:${computed.getPropertyValue(prop)};`)
        .join('')
      const existing = targetEl.getAttribute('style')
      targetEl.setAttribute('style', existing ? `${existing};${styleText}` : styleText)
    } catch (error) {
      // ignore style copy failures caused by inaccessible computed styles
    }

    const sourceChildren = getElementChildren(sourceEl)
    const targetChildren = getElementChildren(targetEl)

    for (let i = 0; i < targetChildren.length; i += 1) {
      inlineComputedStyle(sourceChildren[i], targetChildren[i])
    }
  }

  const inlineForeignObjectStyles = (svgEl, g) => {
    if (!svgEl || !g) return
    const sourceSVG = g.container?.querySelector?.('svg')
    if (!sourceSVG) return

    const sourceBodies = Array.from(sourceSVG.querySelectorAll('foreignObject > body'))
    const targetBodies = Array.from(svgEl.querySelectorAll('foreignObject > body'))

    targetBodies.forEach((targetBody, index) => {
      inlineComputedStyle(sourceBodies[index], targetBody)
    })
  }

  const mergeExportOptions = (options, g) => {
    const merged = { ...options }
    if (merged.copyStyles === undefined) merged.copyStyles = true
    if (merged.preserveDimensions === undefined) merged.preserveDimensions = true
    const userBeforeSerialize = merged.beforeSerialize

    merged.beforeSerialize = function beforeSerialize(svgEl) {
      try {
        inlineForeignObjectStyles(svgEl, g)
      } catch (error) {
        // ignore failures here and continue with export
      }

      if (typeof userBeforeSerialize === 'function') {
        const result = userBeforeSerialize.call(this, svgEl)
        if (result instanceof SVGSVGElement) {
          return result
        }
      }

      return svgEl
    }

    return merged
  }

  const normalizeArgs = (fileNameOrOptions, maybeOptions) => {
    if (typeof fileNameOrOptions === 'string' || typeof fileNameOrOptions === 'number') {
      return [fileNameOrOptions, maybeOptions || {}]
    }
    if (fileNameOrOptions && typeof fileNameOrOptions === 'object') {
      return [undefined, fileNameOrOptions]
    }
    return [undefined, maybeOptions || {}]
  }

  const toSVGString = async (options = {}) => {
    const g = ensureGraph()
    ensureExportPlugin(g)

    const run = (opts) =>
      new Promise((resolve, reject) => {
        try {
          g.toSVG((svg) => resolve(svg), opts)
        } catch (error) {
          reject(error)
        }
      })

    const mergedOptions = mergeExportOptions(options, g)

    try {
      return await run(mergedOptions)
    } catch (error) {
      if (mergedOptions.copyStyles !== false) {
        return run({ ...mergedOptions, copyStyles: false })
      }
      throw error
    }
  }

  const toDataURL = async (type = 'image/png', options = {}) => {
    const normalized = typeof type === 'string' ? type.toLowerCase() : 'image/png'
    const g = ensureGraph()
    ensureExportPlugin(g)
    const method = normalized.includes('jpeg') || normalized.includes('jpg') ? 'toJPEG' : 'toPNG'

    const mergedOptions = mergeExportOptions(options, g)

    if (typeof g[method] !== 'function') {
      throw new Error(
        `Graph export plugin is missing method ${method}. Did you forget to include <XFlowExport />?`
      )
    }

    return new Promise((resolve, reject) => {
      try {
        g[method]((dataUri) => resolve(dataUri), mergedOptions)
      } catch (error) {
        reject(error)
      }
    })
  }

  const exportPNG = (fileNameOrOptions, options = {}) => {
    const g = ensureGraph()
    ensureExportPlugin(g)
    const [fileName, exportOptions] = normalizeArgs(fileNameOrOptions, options)
    const mergedOptions = mergeExportOptions(exportOptions, g)
    const name = fileName || 'graph.png'
    g.exportPNG(name, mergedOptions)
    return name
  }

  const exportJPEG = (fileNameOrOptions, options = {}) => {
    const g = ensureGraph()
    ensureExportPlugin(g)
    const [fileName, exportOptions] = normalizeArgs(fileNameOrOptions, options)
    const mergedOptions = mergeExportOptions(exportOptions, g)
    const name = fileName || 'graph.jpg'
    g.exportJPEG(name, mergedOptions)
    return name
  }

  const exportSVG = async (fileNameOrOptions, options = {}) => {
    const g = ensureGraph()
    ensureExportPlugin(g)
    const [fileName, exportOptions] = normalizeArgs(fileNameOrOptions, options)
    const baseName = fileName != null ? String(fileName) : 'graph.svg'
    const name = baseName.endsWith('.svg') ? baseName : `${baseName}.svg`

    const svgString = await toSVGString({ preserveDimensions: true, ...exportOptions })
    if (!svgString) return null
    const xml = svgString.startsWith('<?xml')
      ? svgString
      : `<?xml version="1.0" encoding="UTF-8"?>\n${svgString}`
    downloadBlob(xml, name, 'image/svg+xml;charset=utf-8')
    return xml
  }

  const exportPDF = async (fileNameOrOptions, options = {}) => {
    const [fileName, exportOptions] = normalizeArgs(fileNameOrOptions, options)
    const {
      type = 'image/png',
      orientation,
      format = 'a4',
      margin = 24,
      pdfOptions = {},
      ...imageOptions
    } = exportOptions || {}

    const normalizedType = typeof type === 'string' ? type.toLowerCase() : 'image/png'
    const dataUrl = await toDataURL(normalizedType, imageOptions)
    if (!dataUrl) return null

    const img = await loadImage(dataUrl)
    const PdfCtor = await ensureJsPDF()

    const orientationHint = orientation || (img.width >= img.height ? 'l' : 'p')
    const pdf = new PdfCtor({ orientation: orientationHint, unit: 'pt', format, ...pdfOptions })

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const horizMargin = typeof margin === 'number' ? margin : (margin?.horizontal ?? 24)
    const vertMargin = typeof margin === 'number' ? margin : (margin?.vertical ?? 24)
    const maxWidth = pageWidth - horizMargin * 2
    const maxHeight = pageHeight - vertMargin * 2
    const scale = Math.min(maxWidth / img.width, maxHeight / img.height, 1)
    const drawWidth = img.width * scale
    const drawHeight = img.height * scale
    const offsetX = (pageWidth - drawWidth) / 2
    const offsetY = (pageHeight - drawHeight) / 2

    const imageType =
      normalizedType.includes('jpeg') || normalizedType.includes('jpg') ? 'JPEG' : 'PNG'
    pdf.addImage(dataUrl, imageType, offsetX, offsetY, drawWidth, drawHeight)

    const saveAs = fileName || 'graph.pdf'
    pdf.save(saveAs)
    return saveAs
  }

  return {
    exportPNG,
    exportJPEG,
    exportSVG,
    exportPDF,
    toDataURL,
    toSVGString
  }
}
