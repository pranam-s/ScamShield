import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { Link } from 'expo-router';

const LandingScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.welcomeText}>Welcome User,</Text>

      <View style={styles.iconContainer}>
        <Link href="/call" style={styles.iconWrapper}>
          <View style={styles.iconCard}>
            <Image
              source={{
                uri: 'https://cdn-icons-png.flaticon.com/512/724/724664.png', // Call icon
              }}
              style={styles.icon}
            />
            <Text style={styles.iconText}>Call</Text>
          </View>
        </Link>

        <Link href="/studyscam" style={styles.iconWrapper}>
          <View style={styles.iconCard}>
            <Image
              source={require('../../assets/images/education.webp')} // Correct path to your image
              style={styles.icon}
              resizeMode="contain"
            />
            <Text style={styles.iconText}>Study Scams</Text>
          </View>
        </Link>
      </View>

      <Image
        source={require('../../assets/images/landing.png')} // Correct path to your image
        style={styles.illustration}
        resizeMode="contain"
      />

      <Text style={styles.infoText}>
        "Legitimate companies won’t ask for sensitive info over the phone."
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    alignItems: 'center',
    padding: 20,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
    marginBottom: 20,
  },
  iconContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
  },
  iconWrapper: {
    alignItems: 'center',
  },
  iconCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
    padding: 15,
    alignItems: 'center',
    width: 120,
    // transition: 'transform 0.2s',
  },
  icon: {
    width: 80,
    height: 80,
    marginBottom: 5,
  },
  iconText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    textAlign: 'center',
  },
  illustration: {
    width: '100%',
    height: 200,
    marginBottom: 20,
    marginTop: 20,
  },
  infoText: {
    fontSize: 14,
    color: '#555',
    textAlign: 'center',
    marginTop: 20,
    paddingHorizontal: 20,
  },
});

export default LandingScreen;