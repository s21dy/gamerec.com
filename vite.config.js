import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
    root: 'src/templates', // Where index.html resides
    base: '/', // Base path for GitHub Pages
    build: {
        outDir: '../../dist', // Output directory relative to src/templates
        emptyOutDir: true,
        rollupOptions: {
            input: resolve(__dirname, 'src/templates/index.html'), // Entry point
        },
    },
});

