import React, { useEffect, useRef } from 'react';
import { BackHandler, Platform, ToastAndroid } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { createNavigationContainerRef } from '@react-navigation/native';
import { FavoritesProvider } from './src/context/FavoritesContext';
import RootNavigator, { RootStackParamList } from './src/navigation/RootNavigator';

const navigationRef = createNavigationContainerRef<RootStackParamList>();
const EXIT_PROMPT_WINDOW_MS = 2000;

function useAndroidDoubleBackToExit() {
  const lastBackPressRef = useRef(0);

  useEffect(() => {
    if (Platform.OS !== 'android') return;

    const onBackPress = () => {
      if (navigationRef.isReady() && navigationRef.canGoBack()) {
        return false;
      }
      const now = Date.now();
      if (now - lastBackPressRef.current < EXIT_PROMPT_WINDOW_MS) {
        BackHandler.exitApp();
        return true;
      }
      lastBackPressRef.current = now;
      ToastAndroid.show('Press back again to exit', ToastAndroid.SHORT);
      return true;
    };

    const subscription = BackHandler.addEventListener('hardwareBackPress', onBackPress);
    return () => subscription.remove();
  }, []);
}

export default function App() {
  useAndroidDoubleBackToExit();

  return (
    <FavoritesProvider>
      <StatusBar style="dark" translucent backgroundColor="transparent" />
      <RootNavigator navigationRef={navigationRef} />
    </FavoritesProvider>
  );
}
