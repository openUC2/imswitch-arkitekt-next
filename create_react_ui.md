**Directory skeleton**

```
imswitch_plugin_lightsheet/
│
├─ ui/
│   ├─ src/
│   │   ├─ LightsheetWidget.jsx
│   │   └─ index.js
│   ├─ public/
│   │   └─ index.html            # only for local dev
│   ├─ package.json
│   └─ webpack.config.js
│
└─ pyproject.toml                # python side
```

---

### 1  Init the frontend folder

```bash
cd src/imswitch_lightsheet
mkdir ui
cd ui
npm init -y
npm i react react-dom
npm i -D webpack webpack-cli webpack-dev-server \
       html-webpack-plugin \
       @babel/core @babel/preset-env @babel/preset-react babel-loader
```

---

### 2  Create `webpack.config.js`

```bash
nano wepack.config.js
```
```js
// ui/webpack.config.js
const HtmlPlugin = require('html-webpack-plugin');
const { ModuleFederationPlugin } = require('webpack').container;
const path = require('path');

module.exports = (_, argv) => ({
  entry: './src/index.js',
  mode: argv.mode || 'development',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    publicPath: 'auto'
  },
  devServer: { port: 3001, historyApiFallback: true },
  module: {
    rules: [{
      test: /\.(js|jsx)$/,
      loader: 'babel-loader',
      exclude: /node_modules/,
      options: { presets: ['@babel/preset-env', '@babel/preset-react'] }
    }]
  },
  plugins: [
    new ModuleFederationPlugin({
      name: 'lightsheet_plugin',           // scope
      filename: 'remoteEntry.js',          // **this** file is what Python serves
      exposes: {
        './Widget': './src/LightsheetWidget.jsx'
      },
      shared: { 
        react:  { singleton: true, eager: true, requiredVersion: false },
        'react-dom': { singleton: true, eager: true, requiredVersion: false }
      }
    }),
    new HtmlPlugin({ template: 'public/index.html' })   // dev only
  ],
  resolve: { extensions: ['.js', '.jsx'] }
});
```

---

### 3  Add source files

```bash
mkdir src
nano src/LightsheetWidget.jsx
```

```jsx
import React from "react";
import { Button } from "@mui/material";

export default function LightsheetWidget({ hostIP, hostPort }) {
  const start = () =>
    fetch(`${hostIP}:${hostPort}/LightsheetController/performScanningRecording`);

  return (
    <div style={{ padding: 16 }}>
      <h3>Lightsheet controller</h3>
      <Button variant="contained" onClick={start}>Start scan</Button>
    </div>
  );
}
```

```bash 
nano src/index.js
```


```js
// Split bootstrap so the host can lazy‑load it
import('./LightsheetWidget');
```

---

### 4  package.json scripts

```bash
nano package.json
```

```jsonc
{
  "name": "lightsheet_plugin_ui",
  "version": "0.1.0",
  "main": "dist/remoteEntry.js",
  "private": true,
  "scripts": {
    "dev":    "webpack serve --mode development",
    "build":  "webpack --mode production"
  }
}
```

---

### 5  Build once

```bash
npm run build              # dist/remoteEntry.js + chunks
```

After this, `ui/dist` contains:

```
remoteEntry.js       <-- what the React shell loads
main.js
123abcde.chunk.js    <-- code‑split chunks
```

---

### 6  Ship files with the wheel

`pyproject.toml`

```toml
[tool.setuptools.package-data]
imswitch_plugin_lightsheet = ["ui/dist/*"]

[project.entry-points."imswitch.ui_plugins"]
lightsheet = "imswitch_plugin_lightsheet:register_ui"
```

`imswitch_plugin_lightsheet/__init__.py`

```python
from importlib.resources import files
from fastapi.staticfiles import StaticFiles

def register_ui(app):
    static = files(__package__).joinpath("ui", "dist")
    mount = "/plugins/lightsheet"
    app.mount(mount, StaticFiles(directory=static), name=mount)
    return {
        "name": "Lightsheet",
        "icon": "ThreeDRotationIcon",
        "remote": f"{mount}/remoteEntry.js",
        "scope": "lightsheet_plugin",
        "exposed": "Widget"
    }
```

---

### 7  Local development with hot reload

```
VITE_REACT_APP_API=http://127.0.0.1:8001  npm run dev
```

(the core server may proxy `/plugins/lightsheet/*` to `localhost:3001` in development if desired).

---

Done: the wheel now contains everything—`remoteEntry.js` and chunks—under `ui/dist/`.
When `pip install imswitch‑plugin‑lightsheet` is executed, the FastAPI wrapper mounts those files and the React host fetches them on the fly.
