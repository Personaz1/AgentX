import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './store';

// Типизированная версия хука useDispatch
export const useAppDispatch = () => useDispatch<AppDispatch>();

// Типизированная версия хука useSelector
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector; 