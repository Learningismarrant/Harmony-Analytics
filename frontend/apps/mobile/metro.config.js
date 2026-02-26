const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "../..");

const config = getDefaultConfig(projectRoot);

// 1. Watch toutes les sources du monorepo (packages internes)
config.watchFolders = [monorepoRoot];

// 2. Résolution des modules : chercher d'abord dans le workspace,
//    puis remonter à la racine du monorepo
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(monorepoRoot, "node_modules"),
];

// 2b. Forcer react-native-screens vers la version locale du workspace.
//     npm hisse react-native-screens@4.24.x à la racine du monorepo (peer dep de
//     @react-navigation/*), mais cette version est incompatible avec Expo SDK 52 :
//     son composant Fabric SearchBarNativeComponent déclare onSearchFocus avec le
//     type "undefined", ce qui est rejeté par le validator Metro en New Architecture.
//     extraNodeModules prend la priorité sur nodeModulesPaths et pointe vers
//     apps/mobile/node_modules/react-native-screens@4.4.0 (version correcte).
config.resolver.extraNodeModules = {
  "react-native-screens": path.resolve(projectRoot, "node_modules/react-native-screens"),
  "react-native-safe-area-context": path.resolve(projectRoot, "node_modules/react-native-safe-area-context"),
};

// 3. Permettre à Metro de résoudre les fichiers .ts depuis node_modules
//    (packages internes exportent directement leur source TypeScript)
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  "ts",
  "tsx",
  "mts",
];

// 4. Activer la résolution du champ "exports" dans les package.json
//    avec les bonnes conditions pour React Native (ex: axios → dist/browser/axios.cjs)
config.resolver.unstable_enablePackageExports = true;
config.resolver.unstable_conditionNames = [
  "require",
  "import",
  "browser",
  "default",
];

module.exports = config;
