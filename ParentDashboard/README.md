# React + Vite Parent Dashboard

This is the central web dashboard for parents to monitor their child's SpellGate activity, manage time banks, and track mastered words.

## Project Setup

This dashboard was built using React and Vite. It uses Firebase for real-time database synchronization (Firestore) and Authentication.

1. **Install Dependencies:**
   ```bash
   npm install
   ```

2. **Run Development Server:**
   ```bash
   npm run dev
   ```

## Firebase Deployment & Hosting

The dashboard is designed to be hosted on Firebase Hosting so it can be securely accessed from anywhere. If you have not yet deployed the site, follow these steps:

1. **Install Firebase CLI (if not already installed):**
   ```bash
   npm install -g firebase-tools
   ```

2. **Login to Firebase:**
   ```bash
   firebase login
   ```

3. **Initialize Firebase in this directory:**
   ```bash
   firebase init hosting
   ```
   *Select your existing SpellGate Firebase project.*
   *When asked for the public directory, type `dist`.*
   *Configure as a single-page app: `Yes`.*
   *Set up automatic builds with GitHub: `No` (or Yes if you want CI/CD).*

4. **Build the Production Dashboard:**
   ```bash
   npm run build
   ```
   *This compiles the Vite app into the `dist` folder.*

5. **Deploy to Firebase:**
   ```bash
   firebase deploy --only hosting
   ```
   *Your live dashboard URL will be provided in the terminal output.*

## Architecture Notes
- **Hosting**: Firebase Hosting (CDN backed, high availability).
- **Backend & DB**: Firebase Firestore (serverless, no maintenance required).
- **Security**: Handled via `firestore.rules` preventing unauthorized writes.
