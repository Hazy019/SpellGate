import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  onAuthStateChanged,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  sendEmailVerification,
  signOut,
} from 'firebase/auth';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { auth, db } from './firebase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });
    return unsub;
  }, []);

  // Register a new parent account
  async function register(email, password) {
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    // Send email verification immediately after signup
    await sendEmailVerification(cred.user);
    // Create the parent's Firestore document skeleton
    await setDoc(doc(db, 'users', cred.user.uid, 'child_data', 'settings'), {
      reward_multiplier: 10,
      force_unlock: false,
      created_at: serverTimestamp(),
    });
    await setDoc(doc(db, 'users', cred.user.uid, 'child_data', 'progress'), {
      mastered_words: [],
      current_level: 'Novice',
      sessions: [],
      created_at: serverTimestamp(),
    });
    return cred.user;
  }

  async function login(email, password) {
    return signInWithEmailAndPassword(auth, email, password);
  }

  async function logout() {
    return signOut(auth);
  }

  async function resendVerification() {
    if (auth.currentUser) {
      return sendEmailVerification(auth.currentUser);
    }
  }

  const value = { user, loading, register, login, logout, resendVerification };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
