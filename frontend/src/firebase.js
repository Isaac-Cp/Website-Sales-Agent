import { initializeApp } from 'firebase/app';
import { getAnalytics, isSupported, logEvent } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: 'AIzaSyC_qO4jr4mCO03tjMWjBLL3jMf2El6Q0l4',
  authDomain: 'delta-51569.firebaseapp.com',
  projectId: 'delta-51569',
  storageBucket: 'delta-51569.firebasestorage.app',
  messagingSenderId: '1080897711290',
  appId: '1:1080897711290:web:7cf1b034154d56f94f6683',
  measurementId: 'G-R98KW588PC',
};

export const firebaseApp = initializeApp(firebaseConfig);

let analyticsInstance = null;

export async function initFirebaseAnalytics() {
  if (typeof window === 'undefined') {
    return null;
  }
  if (analyticsInstance) {
    return analyticsInstance;
  }
  try {
    const supported = await isSupported();
    if (!supported) {
      return null;
    }
    analyticsInstance = getAnalytics(firebaseApp);
    return analyticsInstance;
  } catch (error) {
    console.warn('Firebase analytics unavailable:', error);
    return null;
  }
}

export async function trackDashboardView() {
  const analytics = await initFirebaseAnalytics();
  if (!analytics) {
    return;
  }
  logEvent(analytics, 'dashboard_view', {
    screen_name: 'sales_agent_dashboard',
  });
}
