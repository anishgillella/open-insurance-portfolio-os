'use client';

import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

// Types
export type UserRole = 'owner' | 'property-manager' | 'lender' | 'broker' | 'consultant';

export type PropertyType =
  | 'multifamily'
  | 'office'
  | 'retail'
  | 'industrial'
  | 'self-storage'
  | 'other';

export type GeographicRegion =
  | 'northeast'
  | 'midwest'
  | 'south'
  | 'west'
  | 'national';

export type SubscriptionPlan = 'monthly' | 'annual';

export interface OnboardingData {
  // Auth
  email: string;
  password: string;

  // Profile
  firstName: string;
  lastName: string;
  companyName: string;
  companyWebsite: string;
  phoneNumber: string;

  // Role
  role: UserRole | null;

  // Portfolio
  propertyCount: string;
  propertyTypes: PropertyType[];
  approximateUnits: string;
  approximateSqFt: string;
  geographicFocus: GeographicRegion[];

  // Upload
  uploadedFiles: File[];
  documentType: string;

  // Subscription
  plan: SubscriptionPlan;
  discountCode: string;

  // Payment
  cardName: string;
  cardNumber: string;
  cardExpiry: string;
  cardCvv: string;
  billingAddress: string;
  billingCity: string;
  billingState: string;
  billingZip: string;
  billingCountry: string;
}

export type OnboardingStep =
  | 'login'
  | 'register'
  | 'verify'
  | 'profile'
  | 'role'
  | 'portfolio'
  | 'upload'
  | 'plan'
  | 'payment'
  | 'complete';

interface OnboardingState {
  currentStep: OnboardingStep;
  completedSteps: OnboardingStep[];
  data: OnboardingData;
  isVerified: boolean;
}

type OnboardingAction =
  | { type: 'SET_STEP'; payload: OnboardingStep }
  | { type: 'COMPLETE_STEP'; payload: OnboardingStep }
  | { type: 'UPDATE_DATA'; payload: Partial<OnboardingData> }
  | { type: 'SET_VERIFIED'; payload: boolean }
  | { type: 'RESET' }
  | { type: 'LOAD_STATE'; payload: OnboardingState };

const initialData: OnboardingData = {
  email: '',
  password: '',
  firstName: '',
  lastName: '',
  companyName: '',
  companyWebsite: '',
  phoneNumber: '',
  role: null,
  propertyCount: '',
  propertyTypes: [],
  approximateUnits: '',
  approximateSqFt: '',
  geographicFocus: [],
  uploadedFiles: [],
  documentType: 'policy',
  plan: 'monthly',
  discountCode: '',
  cardName: '',
  cardNumber: '',
  cardExpiry: '',
  cardCvv: '',
  billingAddress: '',
  billingCity: '',
  billingState: '',
  billingZip: '',
  billingCountry: 'US',
};

const initialState: OnboardingState = {
  currentStep: 'login',
  completedSteps: [],
  data: initialData,
  isVerified: false,
};

function onboardingReducer(
  state: OnboardingState,
  action: OnboardingAction
): OnboardingState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, currentStep: action.payload };

    case 'COMPLETE_STEP':
      if (state.completedSteps.includes(action.payload)) {
        return state;
      }
      return {
        ...state,
        completedSteps: [...state.completedSteps, action.payload],
      };

    case 'UPDATE_DATA':
      return {
        ...state,
        data: { ...state.data, ...action.payload },
      };

    case 'SET_VERIFIED':
      return { ...state, isVerified: action.payload };

    case 'RESET':
      return initialState;

    case 'LOAD_STATE':
      return action.payload;

    default:
      return state;
  }
}

interface OnboardingContextValue {
  state: OnboardingState;
  setStep: (step: OnboardingStep) => void;
  completeStep: (step: OnboardingStep) => void;
  updateData: (data: Partial<OnboardingData>) => void;
  setVerified: (verified: boolean) => void;
  reset: () => void;
  nextStep: () => void;
  prevStep: () => void;
  canProceed: (step: OnboardingStep) => boolean;
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

const STORAGE_KEY = 'openinsurance_onboarding';

// Step order for navigation
const stepOrder: OnboardingStep[] = [
  'login',
  'register',
  'verify',
  'profile',
  'role',
  'portfolio',
  'upload',
  'plan',
  'payment',
  'complete',
];

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(onboardingReducer, initialState);

  // Load state from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Don't restore uploaded files from localStorage (they can't be serialized)
        parsed.data.uploadedFiles = [];
        dispatch({ type: 'LOAD_STATE', payload: parsed });
      }
    } catch (error) {
      console.error('Failed to load onboarding state:', error);
    }
  }, []);

  // Save state to localStorage on changes
  useEffect(() => {
    try {
      // Create a version without files for storage
      const stateToSave = {
        ...state,
        data: {
          ...state.data,
          uploadedFiles: [], // Don't save files
        },
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    } catch (error) {
      console.error('Failed to save onboarding state:', error);
    }
  }, [state]);

  const setStep = (step: OnboardingStep) => {
    dispatch({ type: 'SET_STEP', payload: step });
  };

  const completeStep = (step: OnboardingStep) => {
    dispatch({ type: 'COMPLETE_STEP', payload: step });
  };

  const updateData = (data: Partial<OnboardingData>) => {
    dispatch({ type: 'UPDATE_DATA', payload: data });
  };

  const setVerified = (verified: boolean) => {
    dispatch({ type: 'SET_VERIFIED', payload: verified });
  };

  const reset = () => {
    dispatch({ type: 'RESET' });
    localStorage.removeItem(STORAGE_KEY);
  };

  const nextStep = () => {
    const currentIndex = stepOrder.indexOf(state.currentStep);
    if (currentIndex < stepOrder.length - 1) {
      completeStep(state.currentStep);
      setStep(stepOrder[currentIndex + 1]);
    }
  };

  const prevStep = () => {
    const currentIndex = stepOrder.indexOf(state.currentStep);
    if (currentIndex > 0) {
      setStep(stepOrder[currentIndex - 1]);
    }
  };

  const canProceed = (step: OnboardingStep): boolean => {
    const stepIndex = stepOrder.indexOf(step);
    const currentIndex = stepOrder.indexOf(state.currentStep);

    // Can always go to completed steps or current step
    if (stepIndex <= currentIndex) return true;

    // Can only go to next step if all previous steps are completed
    for (let i = 0; i < stepIndex; i++) {
      if (!state.completedSteps.includes(stepOrder[i])) {
        return false;
      }
    }
    return true;
  };

  return (
    <OnboardingContext.Provider
      value={{
        state,
        setStep,
        completeStep,
        updateData,
        setVerified,
        reset,
        nextStep,
        prevStep,
        canProceed,
      }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}

// Helper to get role-specific labels
export function getRoleLabels(role: UserRole | null) {
  switch (role) {
    case 'owner':
      return {
        countLabel: 'Number of Properties Owned',
        unitsLabel: 'Approximate Units Owned',
        sqftLabel: 'Approximate Square Footage Owned',
        typesLabel: 'Property Types Owned',
      };
    case 'property-manager':
      return {
        countLabel: 'Number of Properties Managed',
        unitsLabel: 'Approximate Units Managed',
        sqftLabel: 'Approximate Square Footage Managed',
        typesLabel: 'Property Types Managed',
      };
    case 'lender':
      return {
        countLabel: 'Number of Properties Actively Financed',
        unitsLabel: 'Approximate Units Financed',
        sqftLabel: 'Approximate Square Footage Financed',
        typesLabel: 'Property Types Financed',
      };
    case 'broker':
      return {
        countLabel: 'Number of Properties Brokered',
        unitsLabel: 'Approximate Units Brokered',
        sqftLabel: 'Approximate Square Footage Brokered',
        typesLabel: 'Property Types Brokered',
      };
    case 'consultant':
      return {
        countLabel: '',
        unitsLabel: '',
        sqftLabel: '',
        typesLabel: 'Property Types Advised On',
      };
    default:
      return {
        countLabel: 'Number of Properties',
        unitsLabel: 'Approximate Units',
        sqftLabel: 'Approximate Square Footage',
        typesLabel: 'Property Types',
      };
  }
}

// Helper to determine if role needs quantity fields
export function roleNeedsQuantities(role: UserRole | null): boolean {
  return role !== 'consultant';
}

// Helper to determine metric type based on property types
export function getMetricType(propertyTypes: PropertyType[]): 'units' | 'sqft' | 'both' {
  const residentialTypes: PropertyType[] = ['multifamily'];
  const commercialTypes: PropertyType[] = ['office', 'retail', 'industrial', 'self-storage'];

  const hasResidential = propertyTypes.some((t) => residentialTypes.includes(t));
  const hasCommercial = propertyTypes.some((t) => commercialTypes.includes(t));

  if (hasResidential && hasCommercial) return 'both';
  if (hasResidential) return 'units';
  return 'sqft';
}
