import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';
import HomeScreen from '../screens/HomeScreen';
import FavoritesScreen from '../screens/FavoritesScreen';
import RecipeDetailScreen from '../screens/RecipeDetailScreen';
import { colors } from '../theme';

export type RootStackParamList = {
  Home: undefined;
  Favorites: undefined;
  RecipeDetail: { id: string };
};

const HomeStack = createNativeStackNavigator<RootStackParamList>();
const FavStack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

function HomeStackNavigator() {
  return (
    <HomeStack.Navigator screenOptions={{ headerShown: false }}>
      <HomeStack.Screen name="Home" component={HomeScreen} />
      <HomeStack.Screen name="RecipeDetail" component={RecipeDetailScreen} />
    </HomeStack.Navigator>
  );
}

function FavoritesStackNavigator() {
  return (
    <FavStack.Navigator screenOptions={{ headerShown: false }}>
      <FavStack.Screen name="Favorites" component={FavoritesScreen} />
      <FavStack.Screen name="RecipeDetail" component={RecipeDetailScreen} />
    </FavStack.Navigator>
  );
}

export default function RootNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: colors.primary,
          tabBarInactiveTintColor: colors.subtext,
          tabBarStyle: { backgroundColor: colors.card, borderTopColor: colors.border },
        }}
      >
        <Tab.Screen
          name="RecipesTab"
          component={HomeStackNavigator}
          options={{
            title: 'Recipes',
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>🍛</Text>,
          }}
        />
        <Tab.Screen
          name="FavoritesTab"
          component={FavoritesStackNavigator}
          options={{
            title: 'Favorites',
            tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>♥</Text>,
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
