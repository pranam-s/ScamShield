import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { Link } from 'expo-router';

export default function FirstScreen() {
  return (
    <View style={styles.container}>
      {/* Illustration */}
      <Image
        source={require('../assets/images/firstImage.png')} // Correct path to your image
        style={styles.image}
      />

      {/* Title */}
      <Text style={styles.title}>
        <Text style={styles.highlight}>Instant Voice Alert</Text> for Scam Calls
      </Text>

      {/* Subtitle */}
      <Text style={styles.subtitle}>
        <Text style={styles.quote}>"Be cautious"</Text> of unknown or international numbers
      </Text>

      {/* Next Button */}
      <Link href="/second" style={styles.button}>
        <Text style={styles.buttonText}>Next</Text>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9', 
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  image: {
    width: '100%', 
    height: '60%',
    resizeMode: 'contain', 
    marginBottom: 30,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#333', 
    marginBottom: 10,
    lineHeight: 34, 
  },
  highlight: {
    color: '#007BFF', 
    fontWeight: 'bold',
    fontSize: 28, 
  },
  subtitle: {
    fontSize: 18,
    textAlign: 'center',
    color: '#555',
    marginBottom: 30,
    paddingHorizontal: 20, 
    lineHeight: 26, 
  },
  quote: {
    fontStyle: 'italic',
    color: '#FF6F61',
    fontWeight: '600', 
  },
  button: {
    backgroundColor: '#007BFF', 
    paddingVertical: 15,
    paddingHorizontal: 100,
    borderRadius: 10,
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 5, 
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff', 
  },
});