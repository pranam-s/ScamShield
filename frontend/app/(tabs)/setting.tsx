import React, { useState } from 'react';
import { View, Text, StyleSheet, Switch, TouchableOpacity } from 'react-native';
import { Link } from 'expo-router';

export default function SettingsScreen() {
  const [useLocalModel, setUseLocalModel] = useState(false);
  const [useCloudModel, setUseCloudModel] = useState(false);
  const [adaptiveLearning, setAdaptiveLearning] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Settings</Text>

      <View style={styles.settingItem}>
        <View style={styles.settingTextContainer}>
          <Text style={styles.settingTitle}>Use Model Locally</Text>
          <Text style={styles.settingDescription}>
            Process everything on your device for maximum privacy.
          </Text>
        </View>
        <Switch
          value={useLocalModel}
          onValueChange={(value) => setUseLocalModel(value)}
        />
      </View>

      <View style={styles.settingItem}>
        <View style={styles.settingTextContainer}>
          <Text style={styles.settingTitle}>Use Model on Cloud</Text>
          <Text style={styles.settingDescription}>
            Hosted model will predict the scam saving device RAM and battery
            usage. Recommended for less memory devices.
          </Text>
        </View>
        <Switch
          value={useCloudModel}
          onValueChange={(value) => setUseCloudModel(value)}
        />
      </View>

      <View style={styles.settingItem}>
        <View style={styles.settingTextContainer}>
          <Text style={styles.settingTitle}>Model Adaptive Learning</Text>
          <Text style={styles.settingDescription}>
            This allows the model to send your conversation to the database for
            model learning purposes in encrypted format.
          </Text>
        </View>
        <Switch
          value={adaptiveLearning}
          onValueChange={(value) => setAdaptiveLearning(value)}
        />
      </View>

      <Link href="/" style={styles.restartButton}>
        <Text style={styles.restartButtonText}>Restart</Text>
      </Link>

    
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  settingTextContainer: {
    flex: 1,
    marginRight: 10,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  settingDescription: {
    fontSize: 14,
    color: '#555',
  },
  restartButton: {
    backgroundColor: '#d3d3d3',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 5,
    alignSelf: 'center',
    marginTop: 20,
  },
  restartButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    paddingVertical: 10,
    borderTopLeftRadius: 15,
    borderTopRightRadius: 15,
    position: 'absolute',
    bottom: 0,
    width: '100%',
  },
  footerIconWrapper: {
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#000',
  },
});