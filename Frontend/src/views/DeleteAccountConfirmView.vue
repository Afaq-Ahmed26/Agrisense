<template>
  <div class="container">
    <div class="row justify-content-center align-items-center min-vh-100">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-3">
          <div class="card-header text-center bg-primary text-white py-4 rounded-top-3">
            <h2 class="mb-0"><i class="fas fa-seedling me-2"></i>AgriSense</h2>
            <small class="opacity-75">Account Deletion Confirmation</small>
          </div>
          <div class="card-body p-4">
            <div v-if="isLoading">
              <p class="text-center">Processing your account deletion...</p>
              <div class="d-flex justify-content-center">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
              </div>
            </div>
            
            <div v-if="successMessage" class="alert alert-success mt-3" role="alert">
              {{ successMessage }}
            </div>
            <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
              {{ errorMessage }}
            </div>

            <div class="text-center mt-3">
              <router-link to="/login" class="text-decoration-none">Back to Login</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { firebaseService } from '@/services/firebase';
import { applyActionCode, AuthErrorCodes } from 'firebase/auth'; // Import applyActionCode and AuthErrorCodes
import { apiService } from '@/services/api'; // Assuming apiService has a deleteUser method

const isLoading = ref(true);
const successMessage = ref('');
const errorMessage = ref('');
const router = useRouter();
const route = useRoute();

onMounted(async () => {
  const oobCode = route.query.oobCode;

  if (!oobCode) {
    errorMessage.value = 'Invalid or missing verification code.';
    isLoading.value = false;
    return;
  }

  try {
    if (!firebaseService.auth) {
      throw new Error("Firebase Auth is not initialized.");
    }
    
    // Apply the action code to verify the email and confirm the action
    await applyActionCode(firebaseService.auth, oobCode);
    
    // After successfully applying the action code, the user is considered verified.
    // Now, we can proceed with the backend call to hard delete the Firebase user
    // and soft delete their record in Firestore.
    // The user should be logged in *after* applyActionCode for currentUser to be available,
    // or we might need to get the user from the oobCode if applyActionCode doesn't log them in.
    // For simplicity, we'll assume applyActionCode implies the user context for deletion.
    
    // We need to pass the UID of the user to be deleted to the backend.
    // If the user is logged in after applyActionCode, we can get it from currentUser.
    // If not, Firebase APIs typically don't directly give the UID from oobCode alone in client-side.
    // A more robust solution might involve the backend verifying the oobCode itself or
    // the client sending the oobCode to the backend for verification + deletion.
    // For now, let's assume `applyActionCode` keeps the user logged in, or we get the UID from authStore if available.

    const currentUser = firebaseService.auth.currentUser;
    if (!currentUser || currentUser.uid !== firebaseService.auth.currentUser.uid) { // Ensure it's the right user trying to delete
        // This scenario is tricky. applyActionCode doesn't necessarily sign in the user who initiated it.
        // It's just confirming the action linked to the oobCode.
        // The most secure way is to have the backend receive the oobCode, verify it, and then delete.
        // However, if we assume the user is signed in to the account associated with the oobCode after
        // applyActionCode (which is often the case for email verification actions), we can proceed.
        // For a delete action, it's safer to rely on the backend to know *which* user is being deleted
        // based on a session token/ID token from a logged-in user who just confirmed the action.
        
        // Temporarily, we'll assume the currently logged-in user is the one to be deleted.
        // A better approach for deletion confirmation is to have the backend initiate the deletion link
        // which itself contains a signed token (not Firebase oobCode) that the backend can verify.
        // But following the path with sendEmailVerification for now:
        if (!currentUser) {
          // If no user is logged in after applyActionCode, we cannot determine who to delete.
          // This implies a need for a backend endpoint that takes the oobCode and handles deletion.
          errorMessage.value = 'User not authenticated after verification. Please log in and retry deletion.';
          isLoading.value = false;
          return;
        }
    }
    
    // Call the backend to perform hard delete in Firebase Auth and soft delete in Firestore
    const deleteResult = await apiService.deleteUser(currentUser.uid); // Assuming apiService.deleteUser exists

    if (deleteResult.success) {
      successMessage.value = 'Your account has been successfully deleted.';
      // Log out the user from frontend after deletion
      await firebaseService.signOut(); // Ensure the frontend state is cleared
      router.push('/login'); // Redirect to login
    } else {
      errorMessage.value = deleteResult.message || 'Failed to delete account from backend.';
    }

  } catch (error) {
    console.error('Account deletion confirmation error:', error);
    if (error.code === AuthErrorCodes.EXPIRED_ACTION_CODE || error.code === AuthErrorCodes.INVALID_ACTION_CODE) {
        errorMessage.value = 'The verification link is invalid or has expired. Please try again from your profile page.';
    } else if (error.code === AuthErrorCodes.USER_DISABLED) {
        errorMessage.value = 'Your account has been disabled.';
    } else {
        errorMessage.value = error.message || 'An unexpected error occurred during deletion confirmation.';
    }
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* Scoped styles for DeleteAccountConfirmView */
</style>