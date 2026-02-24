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

// 3. Permettre à Metro de résoudre les fichiers .ts depuis node_modules
//    (packages internes exportent directement leur source TypeScript)
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  "ts",
  "tsx",
  "mts",
];

module.exports = config;
