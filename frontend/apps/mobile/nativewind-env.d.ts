/// <reference types="nativewind/types" />

// NativeWind v4 augments React Native component types to accept className.
// react-native-css-interop/types.d.ts lives in the monorepo root node_modules
// and VS Code's TS server can't reliably follow the reference chain across
// the monorepo boundary. We re-declare it inline here instead.

import "react-native";
declare module "react-native" {
  interface ViewProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface TextProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface TextInputProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface ImagePropsBase {
    className?: string;
    cssInterop?: boolean;
  }
  interface TouchableWithoutFeedbackProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface SwitchProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface StatusBarProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface InputAccessoryViewProps {
    className?: string;
    cssInterop?: boolean;
  }
  interface KeyboardAvoidingViewProps {
    contentContainerClassName?: string;
  }
  interface ScrollViewProps {
    contentContainerClassName?: string;
    indicatorClassName?: string;
  }
  interface FlatListProps<ItemT> {
    columnWrapperClassName?: string;
    contentContainerClassName?: string;
  }
  interface ImageBackgroundProps {
    imageClassName?: string;
  }
}
