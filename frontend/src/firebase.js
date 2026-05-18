import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getAnalytics, isSupported } from "firebase/analytics";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBajpAGANdcJwQstSeEpiA49g1WsoqFWLU",
    authDomain: "nextstep-45524.firebaseapp.com",
    projectId: "nextstep-45524",
    storageBucket: "nextstep-45524.firebasestorage.app",
    messagingSenderId: "409161919716",
    appId: "1:409161919716:web:1156c74bb37d384dc890f1",
    measurementId: "G-40W1HBR1YT"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Safely initialize Analytics only if supported (gracefully handles ad-blockers)
isSupported().then(supported => {
    if (supported) getAnalytics(app);
}).catch(() => { /* silently ignore */ });

const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider };
export default app;
