import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import path from 'path'
import type { PluginOption } from 'vite'

export default function createSvgIcon(isBuild: boolean): PluginOption {
    return createSvgIconsPlugin({
		iconDirs: [path.resolve(process.cwd(), 'src/assets/icons/svg')],
        symbolId: 'icon-[dir]-[name]',
        svgoOptions: isBuild
    })
}
