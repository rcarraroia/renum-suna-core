import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { createClient } from '@supabase/supabase-js';
import { create } from 'zustand';
import { Admin } from '../types/admin';

// Tipos
interface AuthState {
  user: Admin | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: Admin | null) => void;
}

// Criar cliente Supabase
const getSupabaseClient = () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
  return createClient(supabaseUrl, supabaseKey);
};

// Store Zustand
const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  error: null,
  login: async (email, password) => {
    try {
      set({ isLoading: true, error: null });
      const supabase = getSupabaseClient();
      
      // Autenticar com Supabase
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw new Error(error.message);
      if (!data.user) throw new Error('Usuário não encontrado');
      
      // Verificar se o usuário é administrador
      const { data: adminData, error: adminError } = await supabase
        .from('renum_admins')
        .select('*')
        .eq('user_id', data.user.id)
        .single();
      
      if (adminError || !adminData) {
        await supabase.auth.signOut();
        throw new Error('Acesso não autorizado. Apenas administradores podem acessar este painel.');
      }
      
      // Definir usuário
      set({
        user: {
          id: adminData.id,
          user_id: data.user.id,
          name: adminData.name,
          email: data.user.email || '',
          role: adminData.role,
          is_active: adminData.is_active,
          last_login: adminData.last_login,
          created_at: adminData.created_at,
          updated_at: adminData.updated_at,
        },
        isLoading: false,
      });
      
      // Atualizar último login
      await supabase
        .from('renum_admins')
        .update({ last_login: new Date().toISOString() })
        .eq('id', adminData.id);
        
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  logout: async () => {
    try {
      const supabase = getSupabaseClient();
      await supabase.auth.signOut();
      set({ user: null });
    } catch (error: any) {
      set({ error: error.message });
    }
  },
  setUser: (user) => set({ user, isLoading: false }),
}));

// Hook personalizado
export const useAuth = () => {
  const { user, isLoading, error, login, logout, setUser } = useAuthStore();
  const router = useRouter();
  
  useEffect(() => {
    const checkUser = async () => {
      try {
        const supabase = getSupabaseClient();
        
        // Verificar sessão atual
        const { data } = await supabase.auth.getSession();
        
        if (data.session?.user) {
          // Verificar se o usuário é administrador
          const { data: adminData, error: adminError } = await supabase
            .from('renum_admins')
            .select('*')
            .eq('user_id', data.session.user.id)
            .single();
          
          if (!adminError && adminData) {
            setUser({
              id: adminData.id,
              user_id: data.session.user.id,
              name: adminData.name,
              email: data.session.user.email || '',
              role: adminData.role,
              is_active: adminData.is_active,
              last_login: adminData.last_login,
              created_at: adminData.created_at,
              updated_at: adminData.updated_at,
            });
          } else {
            setUser(null);
          }
        } else {
          setUser(null);
        }
      } catch (error) {
        setUser(null);
      }
    };
    
    checkUser();
    
    // Configurar listener para mudanças de autenticação
    const supabase = getSupabaseClient();
    const { data: authListener } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        // Verificar se o usuário é administrador
        const { data: adminData, error: adminError } = await supabase
          .from('renum_admins')
          .select('*')
          .eq('user_id', session.user.id)
          .single();
        
        if (!adminError && adminData) {
          setUser({
            id: adminData.id,
            user_id: session.user.id,
            name: adminData.name,
            email: session.user.email || '',
            role: adminData.role,
            is_active: adminData.is_active,
            last_login: adminData.last_login,
            created_at: adminData.created_at,
            updated_at: adminData.updated_at,
          });
          
          // Atualizar último login
          await supabase
            .from('renum_admins')
            .update({ last_login: new Date().toISOString() })
            .eq('id', adminData.id);
            
        } else {
          setUser(null);
          router.push('/login');
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        router.push('/login');
      }
    });
    
    return () => {
      authListener.subscription.unsubscribe();
    };
  }, [setUser, router]);
  
  return { user, isLoading, error, login, logout };
};