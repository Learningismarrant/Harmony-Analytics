const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");
const path = require("path");

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "../..");

const config = getDefaultConfig(projectRoot);

// 1. Watch toutes les sources du monorepo (packages internes).
//    getDefaultConfig détecte déjà le workspace root et ajoute packages/* et apps/*,
//    mais on étend manuellement pour inclure le dossier node_modules racine.
config.watchFolders = [
  ...config.watchFolders,
  path.resolve(monorepoRoot, "node_modules"),
];

// 2. Résolution des modules : chercher d'abord dans le workspace mobile,
//    puis remonter à la racine du monorepo.
//    getDefaultConfig le fait déjà via getModulesPaths() — on surcharge uniquement
//    pour être explicite et s'assurer que l'ordre est correct.
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(monorepoRoot, "node_modules"),
];

// 3. Permettre à Metro de résoudre les fichiers .ts depuis node_modules
//    (packages internes exportent directement leur source TypeScript)
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  "ts",
  "tsx",
  "mts",
];

// Note: unstable_enablePackageExports est délibérément DÉSACTIVÉ.
// nativewind@4.1.23 a un exports:{} vide — avec package exports activé, Metro
// ne peut pas résoudre nativewind/jsx-runtime (injecté dans chaque fichier JSX
// par jsxImportSource:"nativewind") → crash silencieux total, écran noir.
//
// Sans package exports, Metro résout axios via main:./dist/node/axios.cjs
// (build Node) qui importe le module natif "crypto" → crash RN.
// On intercepte axios via resolveRequest pour forcer le build browser.

config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (moduleName === "axios") {
    return {
      filePath: path.resolve(monorepoRoot, "node_modules/axios/dist/browser/axios.cjs"),
      type: "sourceFile",
    };
  }
  return context.resolveRequest(context, moduleName, platform);
};

// withNativeWind sets up the CSS transformer and NativeWind runtime.
// Without it, className props produce empty style objects → invisible components.
module.exports = withNativeWind(config, { input: "./global.css" });
