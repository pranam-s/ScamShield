import React from 'react';
import { Text, View, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Link } from 'expo-router';

export default function Index() {
  return (
    <View style={styles.container}>
      
      <View style={styles.logoContainer}>
        <Image
          source={require('@/assets/images/scamshield.jpg')} 
          style={styles.logo}
          resizeMode="contain"
        />
        <Text style={styles.title}>Block Scam, Stay safe</Text>
      </View>

     
      
      <Text style={styles.subtitle}>
        "Stay safe from fraudulent calls. Detect and avoid scams easily."
      </Text>

      
      <View style={styles.bottomContainer}>
        <TouchableOpacity style={styles.callButton}>
          <Image
            source={{
              uri: 'https://cdn-icons-png.flaticon.com/512/724/724664.png', 
            }}
            style={styles.callIcon}
          />
          <Link href="/first" style={styles.link}>
            <Text style={styles.callText}>Detect Scam Calls</Text>
          </Link>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff', 
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    position: 'relative',
    marginBottom: 50,
  },
  logo: {
    width: 300, 
    height: 300, 
  },
  magnifyingGlass: {
    position: 'absolute',
    width: 80, 
    height: 80,
    top: 60, 
    left: 120, 
    opacity: 0.8, 
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333333', 
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666666', 
    textAlign: 'center',
    marginBottom: 30,
  },
  bottomContainer: {
    position: 'absolute',
    bottom: 30, 
    alignItems: 'center',
    width: '100%',
  },
  callButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007BFF', 
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  callIcon: {
    width: 30,
    height: 30,
    marginRight: 10,
  },
  callText: {
    fontSize: 18,
    color: '#ffffff', 
    fontWeight: 'bold',
  },
  link: {
    textDecorationLine: 'none', 
  },
});