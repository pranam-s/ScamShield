import React from 'react';
import { View, Text, StyleSheet, Image, ScrollView } from 'react-native';
import { Link } from 'expo-router';

export default function ScamStudyScreen() {
  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header Section */}
        <View style={styles.headerContainer}>
          <Text style={styles.header}>Education Module</Text>
          <Text style={styles.subHeader}>
            Learn how to identify and avoid fraudulent and fake calls.
          </Text>
        </View>

        {/* Section 1: Introduction */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Introduction</Text>
          <Text style={styles.sectionText}>
            Fraudulent and fake calls have become a pervasive issue in India, posing significant
            threats to individuals, businesses, and the economy. This module provides an in-depth
            analysis of the challenges, emerging trends, and countermeasures related to fraud and
            fake calls.
          </Text>
          <Image
                    source={require('../assets/images/scamcalls.jpg')} // Correct path to your image
                    style={styles.image}
                  />
        </View>

        {/* Section 2: Common Tactics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Common Tactics Used by Scammers</Text>
          <View style={styles.bulletContainer}>
            <Text style={styles.bulletPoint}>🔴 Caller ID Spoofing</Text>
            <Text style={styles.bulletPoint}>🔴 Creating a Sense of Urgency</Text>
            <Text style={styles.bulletPoint}>🔴 Impersonating Trusted Entities</Text>
            <Text style={styles.bulletPoint}>🔴 Reward or Prize Scams</Text>
            <Text style={styles.bulletPoint}>🔴 Fake Investment Opportunities</Text>
          </View>
          <Image
                    source={require('../assets/images/scamcallers.jpg')} // Correct path to your image
                    style={styles.image}
                  />
        </View>

        {/* Section 3: Psychological Impact */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Psychological and Emotional Impact</Text>
          <Text style={styles.sectionText}>
            Fake calls can have a significant psychological and emotional impact on victims,
            including feelings of betrayal, anxiety, and financial insecurity. It is important to
            seek support and report incidents to prevent further victimization.
          </Text>
          <Image
                    source={require('../assets/images/pshychology.jpg')} // Correct path to your image
                    style={styles.image}
                  />
        </View>

        {/* Section 4: Countermeasures */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Countermeasures</Text>
          <View style={styles.bulletContainer}>
            <Text style={styles.bulletPoint}>✔️ Use call filtering and authentication systems.</Text>
            <Text style={styles.bulletPoint}>✔️ Verify the authenticity of callers.</Text>
            <Text style={styles.bulletPoint}>✔️ Avoid sharing personal information over the phone.</Text>
            <Text style={styles.bulletPoint}>✔️ Report suspicious calls to authorities.</Text>
          </View>
          <Image
                    source={require('../assets/images/scamdetect.png')} // Correct path to your image
                    style={styles.image}
                  />
        </View>

        {/* Footer Section */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Stay informed and protect yourself from fraudulent activities.
          </Text>
          <Link href="/(tabs)/landing" style={styles.footerButton}>
            <Text style={styles.footerButtonText}>Home</Text>
          </Link>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9', // Light gray background for a clean look
  },
  scrollContent: {
    padding: 20,
  },
  headerContainer: {
    backgroundColor: '#007BFF', // Blue background for the header
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff', // White text for contrast
    textAlign: 'center',
  },
  subHeader: {
    fontSize: 16,
    color: '#f0f8ff', // Light text for a softer look
    textAlign: 'center',
    marginTop: 10,
  },
  section: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    shadowColor: '#000', // Shadow for depth
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 3, // Shadow for Android
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333', // Neutral dark color
    marginBottom: 10,
  },
  sectionText: {
    fontSize: 16,
    color: '#555', // Softer gray for readability
    lineHeight: 24,
    marginBottom: 15,
  },
  bulletContainer: {
    marginBottom: 15,
  },
  bulletPoint: {
    fontSize: 16,
    color: '#555',
    marginBottom: 10,
    lineHeight: 24,
  },
  image: {
    width: '70%',
    height: 300,
    borderRadius: 10,
    marginBottom: 15,
  },
  footer: {
    backgroundColor: '#007BFF',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 20,
  },
  footerText: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 10,
  },
  footerButton: {
    backgroundColor: '#fff',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 5,
  },
  footerButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007BFF',
  },
});