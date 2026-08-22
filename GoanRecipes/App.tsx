import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { FavoritesProvider } from './src/context/FavoritesContext';
import RootNavigator from './src/navigation/RootNavigator';

export default function App() {
  return (
    <FavoritesProvider>
      <StatusBar style="dark" />
      <RootNavigator />
    </FavoritesProvider>
  );
}
