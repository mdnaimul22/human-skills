import { useState, useEffect } from 'react';

/**
 * A reactive hook that reads and writes values to chrome.storage.local.
 * It also listens to external updates (e.g. from background worker or other extension pages) and synchronizes.
 */
export function useChromeStorage<T>(key: string, initialValue: T): [T, (val: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  // Load initial value from chrome storage
  useEffect(() => {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      chrome.storage.local.get([key], (result) => {
        if (result[key] !== undefined) {
          setStoredValue(result[key]);
        }
      });
    }
  }, [key]);

  // Listen for storage changes from other parts of the extension
  useEffect(() => {
    const handleStorageChange = (changes: { [key: string]: chrome.storage.StorageChange }, areaName: string) => {
      if (areaName === 'local' && changes[key]) {
        setStoredValue(changes[key].newValue);
      }
    };

    if (typeof chrome !== 'undefined' && chrome.storage) {
      chrome.storage.onChanged.addListener(handleStorageChange);
      return () => {
        chrome.storage.onChanged.removeListener(handleStorageChange);
      };
    }
  }, [key]);

  // Update value in chrome storage
  const setValue = (value: T | ((prev: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);

      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ [key]: valueToStore });
      }
    } catch (error) {
      console.error('Error setting chrome.storage.local key: ' + key, error);
    }
  };

  return [storedValue, setValue];
}
