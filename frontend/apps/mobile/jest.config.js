module.exports = {
  preset: "jest-expo",
  setupFilesAfterEnv: ["./jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    // Force single React instance — root has v18, local has v19.
    // Without this, hooks crash with "Cannot read properties of null (reading 'useRef')"
    // (same fix as apps/web — see web jest.config.ts moduleNameMapper)
    "^react$": "<rootDir>/node_modules/react",
    "^react/jsx-runtime$": "<rootDir>/node_modules/react/jsx-runtime",
    "^react-test-renderer$": "<rootDir>/node_modules/react-test-renderer",
    // Force single react-native instance — @testing-library/react-native (root) resolves
    // react-native to the ROOT copy (RN 0.73), but our mocks target the LOCAL copy (RN 0.83).
    // Without this, ROOT TurboModuleRegistry.getEnforcing() is called unmocked and throws.
    "^react-native$": "<rootDir>/node_modules/react-native",
    "^react-native/(.*)$": "<rootDir>/node_modules/react-native/$1",
  },
  testMatch: ["**/*.test.{ts,tsx}"],
  // Extend jest-expo's default to also transform @harmony/* workspace packages
  transformIgnorePatterns: [
    "node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|nativewind|react-native-css-interop|@harmony/.*)",
  ],
};
