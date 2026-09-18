import { Tabs } from 'expo-router';
import React from 'react';
import { Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';  // Import Ionicons for the icons

import { HapticTab } from '@/components/HapticTab';
import TabBarBackground from '@/components/ui/TabBarBackground';
import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

export default function TabLayout() {
  // RN 0.85+ reports 'unspecified' when no theme is set; resolve to light.
  const colorScheme = useColorScheme() === 'dark' ? 'dark' : 'light';

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme].tint,  // Active tab color
        tabBarInactiveTintColor: Colors[colorScheme].icon,  // Inactive tab color
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarBackground: TabBarBackground,
        tabBarStyle: Platform.select({
          ios: {
            position: 'absolute',  // iOS specific style for transparency effect
          },
          default: {},
        }),
      }}
    >
      {/* Home Tab */}
      <Tabs.Screen
        name="landing"  // This should be the route for landing.tsx
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <Ionicons size={28} name="home" color={color} />,  // Home icon from Ionicons
        }}
      />

      {/* History Tab */}
      <Tabs.Screen
        name="history"  // Assuming history.tsx will be your screen for History
        options={{
          title: 'History',
          tabBarIcon: ({ color }) => <Ionicons size={28} name="time" color={color} />,  // Clock icon for History
        }}
      />

      {/* Settings Tab */}
      <Tabs.Screen
        name="setting"  // Assuming settings.tsx will be your screen for Settings
        options={{
          title: 'Settings',
          tabBarIcon: ({ color }) => <Ionicons size={28} name="settings" color={color} />,  // Gear icon for Settings (settings)
        }}
      />
    </Tabs>
  );
}
