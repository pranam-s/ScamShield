// This file is a fallback for using MaterialIcons on Android and web.

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { SymbolWeight } from 'expo-symbols';
import React from 'react';
import { OpaqueColorValue, StyleProp, ViewStyle } from 'react-native';

// SF Symbol names this component understands. Kept as an explicit union
// because expo-symbols' SymbolViewProps['name'] grew platform-map object
// members in SDK 57 and can no longer index a Record directly.
export type SFSymbolName =
  | 'house.fill'
  | 'paperplane.fill'
  | 'chevron.left.forwardslash.chevron.right'
  | 'chevron.right';

// Add your SFSymbol to MaterialIcons mappings here.
const MAPPING: Record<SFSymbolName, React.ComponentProps<typeof MaterialIcons>['name']> = {
  // See MaterialIcons here: https://icons.expo.fyi
  // See SF Symbols in the SF Symbols app on Mac.
  'house.fill': 'home',
  'paperplane.fill': 'send',
  'chevron.left.forwardslash.chevron.right': 'code',
  'chevron.right': 'chevron-right',
};

export type IconSymbolName = keyof typeof MAPPING;

/**
 * An icon component that uses native SFSymbols on iOS, and MaterialIcons on Android and web. This ensures a consistent look across platforms, and optimal resource usage.
 *
 * Icon `name`s are based on SFSymbols and require manual mapping to MaterialIcons.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<ViewStyle>;
  weight?: SymbolWeight;
}) {
  return <MaterialIcons color={color} size={size} name={MAPPING[name]} style={style} />;
}
