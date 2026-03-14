import { initializeApp } from "firebase/app"
import { getAuth, GoogleAuthProvider } from "firebase/auth"

const firebaseConfig = {
  apiKey: "AIzaSyDNO-znJv3hMvwD_GqA6OSz8-O5Rdoaelk",
  authDomain: "nexus-agent-6630e.firebaseapp.com",
  projectId: "nexus-agent-6630e",
  storageBucket: "nexus-agent-6630e.firebasestorage.app",
  messagingSenderId: "104514386591",
  appId: "1:104514386591:web:27f120db324a507c6d80aa"
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()
export default app