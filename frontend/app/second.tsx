import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { Link } from 'expo-router';

export default function SecondScreen() {
  return (
    <View style={styles.container}>
      {/* Illustration */}
      <Image
        source={require('../assets/images/secondImage.png')} // Correct path to your image
        style={styles.image}
      />

      {/* Title */}
      <Text style={styles.title}>
        <Text style={styles.highlight}>Choose</Text> How Your Data Will Be Used
      </Text>

      {/* Subtitle */}
      <Text style={styles.subtitle}>
        <Text style={styles.quote}>"Avoid pressure tactics"</Text> — take time to think
      </Text>

      {/* Next Button */}
      <Link href="/third" style={styles.button}>
        <Text style={styles.buttonText}>Next</Text>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9', // Light gray background for a clean look
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  image: {
    width: '100%', // Reduced width to fit better
    height: '60%', // Keep the height the same
    resizeMode: 'contain', // Maintain aspect ratio
    marginBottom: 15,
  },
  title: {
    fontSize: 24, // Larger font size for the title
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#333', // Neutral dark color for better readability
    marginBottom: 10,
    lineHeight: 32, // Adds spacing between lines for better readability
  },
  highlight: {
    color: '#007BFF', // Blue color to highlight important words
    fontWeight: 'bold',
    fontSize: 26, // Slightly larger font size for emphasis
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    color: '#555', // Softer gray for a subtle look
    marginBottom: 30,
    paddingHorizontal: 20, // Adds padding for better alignment
    lineHeight: 24, // Improves readability
  },
  quote: {
    fontStyle: 'italic',
    color: '#FF6F61', // Highlighted color for the quote
    fontWeight: '600', // Slightly bold for emphasis
  },
  button: {
    backgroundColor: '#007BFF', // Blue button for a modern look
    paddingVertical: 15,
    paddingHorizontal: 100,
    borderRadius: 10,
    shadowColor: '#000', // Adds shadow for depth
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 5, // Shadow for Android
    alignItems: 'center',
    marginBottom: -20,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff', // White text for contrast
  },
});