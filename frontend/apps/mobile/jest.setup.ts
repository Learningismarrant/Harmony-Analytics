// ── RN 0.83: BatchedBridge invariant ─────────────────────────────────────
// @testing-library/react-native (in root node_modules) loads the ROOT copy of
// react-native via relative requires that bypass our jest.mock() intercept.
// NativeModules.js:184 checks global.__fbBatchedBridgeConfig at load time.
// Setting it here (before any test code requires react-native internals)
// satisfies the invariant for ALL copies of NativeModules.js.
(global as unknown as Record<string, unknown>).__fbBatchedBridgeConfig = {
  remoteModuleConfig: [],
  localModulesConfig: [],
};

// ── expo-secure-store ──────────────────────────────────────────────────────
jest.mock("expo-secure-store", () => ({
  setItemAsync: jest.fn().mockResolvedValue(undefined),
  getItemAsync: jest.fn().mockResolvedValue(null),
  deleteItemAsync: jest.fn().mockResolvedValue(undefined),
  WHEN_UNLOCKED: "WhenUnlocked",
}));

// ── React Native 0.76 TurboModule compatibility ───────────────────────────
// In RN 0.76 New Architecture, View initialization triggers:
//   NativeComponentRegistry → Platform.ios.js → NativePlatformConstantsIOS
//   → TurboModuleRegistry.getEnforcing('PlatformConstants')
// react-native/jest/setup.js's NativeModules mock doesn't intercept this path
// in Jest v29. Mock TurboModuleRegistry directly so getEnforcing never throws.
// NOTE: all vars must live inside the factory — jest.mock() is hoisted above
// module-level declarations, putting them in the temporal dead zone.
jest.mock("react-native/Libraries/TurboModule/TurboModuleRegistry", () => {
  const dims = { width: 390, height: 844, scale: 2, fontScale: 1 };
  const platformConstants = {
    isTesting: true,
    reactNativeVersion: { major: 0, minor: 76, patch: 0 },
    getConstants: () => ({
      isTesting: true,
      reactNativeVersion: { major: 0, minor: 76, patch: 0 },
      osVersion: "17.0",
      systemName: "iOS",
      interfaceIdiom: "handset",
      forceTouchAvailable: false,
    }),
  };
  // DeviceInfo.getConstants().Dimensions is destructured by Dimensions.js at module load time.
  const deviceInfo = {
    getConstants: jest.fn(() => ({
      Dimensions: { window: dims, screen: dims },
      isIPhoneX_deprecated: false,
    })),
  };
  return {
    get: jest.fn((name: string) => {
      if (name === "PlatformConstants") return platformConstants;
      if (name === "DeviceInfo") return deviceInfo;
      // Return a non-null stub for any other module (e.g. KeyboardObserver, Appearance).
      // NativeEventEmitter throws if get() returns null.
      // Appearance.js calls getColorScheme() at module load time via react-native-css-interop.
      return {
        getConstants: jest.fn(() => ({})),
        addListener: jest.fn(),
        removeListeners: jest.fn(),
        getColorScheme: jest.fn(() => null),
        setColorScheme: jest.fn(),
      };
    }),
    getEnforcing: jest.fn((name: string) => {
      if (name === "PlatformConstants") return platformConstants;
      if (name === "DeviceInfo") return deviceInfo;
      // Generic fallback: any remaining module may call .getConstants()
      return { getConstants: jest.fn(() => ({})) };
    }),
  };
});

// ── UIManager — react-native/jest/setup.js uses relative paths that don't ──
// resolve correctly from a setupFile context. Re-mock with absolute path so
// TouchableOpacity / View initialization never reaches PaperUIManager which
// requires __fbBatchedBridgeConfig (old bridge, not available in New Arch).
jest.mock("react-native/Libraries/ReactNative/UIManager", () => ({
  blur: jest.fn(),
  createView: jest.fn(),
  customBubblingEventTypes: {},
  customDirectEventTypes: {},
  dispatchViewManagerCommand: jest.fn(),
  focus: jest.fn(),
  getViewManagerConfig: jest.fn(() => ({ Commands: {} })),
  hasViewManagerConfig: jest.fn(() => false),
  measure: jest.fn(),
  manageChildren: jest.fn(),
  removeSubviews: jest.fn(),
  setChildren: jest.fn(),
  updateView: jest.fn(),
}));

// ── NativeWind — bypass className/interop processing in tests ────────────
// babel.config.js: jsxImportSource:"nativewind" + nativewind/babel (css-interop).
// css-interop's babel plugin transforms ALL React.createElement() calls to
// createInteropElement() — not just JSX syntax. createInteropElement must
// therefore have the same signature as React.createElement: (type, props, ...children).
// Using r.jsx would break null-props calls and mis-route the children arg as key.
jest.mock("nativewind/jsx-runtime", () => {
  const r = require("react/jsx-runtime");
  return { ...r, createInteropElement: require("react").createElement };
});
jest.mock("nativewind/jsx-dev-runtime", () => {
  const r = require("react/jsx-dev-runtime");
  return { ...r, createInteropElement: require("react").createElement };
});
jest.mock("react-native-css-interop/jsx-runtime", () => {
  const r = require("react/jsx-runtime");
  return { ...r, createInteropElement: require("react").createElement };
});

// ── expo-router ───────────────────────────────────────────────────────────
jest.mock("expo-router", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  })),
  useLocalSearchParams: jest.fn(() => ({})),
  useFocusEffect: jest.fn(),
  Stack: { Screen: jest.fn(() => null) },
}));

// ── react-native-svg ──────────────────────────────────────────────────────
// All locals must live inside the factory (jest.mock() is hoisted — outer
// vars are in the TDZ when the factory runs).
jest.mock("react-native-svg", () => {
  const mockR = require("react");
  const mockSvg      = (p: object) => mockR.createElement("Svg",            p);
  const mockCircle   = (p: object) => mockR.createElement("Circle",         p);
  const mockG        = (p: object) => mockR.createElement("G",              p);
  const mockText     = (p: object) => mockR.createElement("SvgText",        p);
  const mockPath     = (p: object) => mockR.createElement("Path",           p);
  const mockPolygon  = (p: object) => mockR.createElement("Polygon",        p);
  const mockLine     = (p: object) => mockR.createElement("Line",           p);
  const mockRect     = (p: object) => mockR.createElement("Rect",           p);
  const mockDefs     = (p: object) => mockR.createElement("Defs",           p);
  const mockLinGrad  = (p: object) => mockR.createElement("LinearGradient", p);
  const mockStop     = (p: object) => mockR.createElement("Stop",           p);
  const mockClip     = (p: object) => mockR.createElement("ClipPath",       p);
  const mockMask     = (p: object) => mockR.createElement("Mask",           p);
  return {
    __esModule: true,
    default:        mockSvg,
    Svg:            mockSvg,
    Circle:         mockCircle,
    G:              mockG,
    Text:           mockText,
    Path:           mockPath,
    Polygon:        mockPolygon,
    Line:           mockLine,
    Rect:           mockRect,
    Defs:           mockDefs,
    LinearGradient: mockLinGrad,
    Stop:           mockStop,
    ClipPath:       mockClip,
    Mask:           mockMask,
  };
});

// ── @expo/vector-icons ────────────────────────────────────────────────────
// vector-icons loads react-native-css-interop → Appearance → NativeEventEmitter
// → Platform.ios.js → TurboModuleRegistry chain that crashes in jsdom.
// Replace with lightweight string stubs — we only test behaviour, not icons.
jest.mock("@expo/vector-icons", () => ({
  Ionicons: "Ionicons",
  MaterialIcons: "MaterialIcons",
  FontAwesome: "FontAwesome",
}));
