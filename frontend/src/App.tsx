import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppLayout } from './components/AppLayout'
import { DashboardPage } from './pages/DashboardPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { MarketplacePage } from './marketplace/MarketplacePage'
import { ItemFormPage } from './marketplace/ItemFormPage'
import { ItemDetailsPage } from './marketplace/ItemDetailsPage'
import { RentalsPage } from './rentals/RentalsPage'

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route element={<LoginPage />} path="login" />
            <Route element={<RegisterPage />} path="register" />
            <Route element={<ProtectedRoute />}>
              <Route element={<MarketplacePage />} path="marketplace" />
              <Route element={<ItemFormPage />} path="items/new" />
              <Route element={<ItemFormPage />} path="items/:id/edit" />
              <Route element={<ItemDetailsPage />} path="items/:id" />
              <Route element={<DashboardPage />} path="app" />
              <Route element={<RentalsPage />} path="rentals" />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
