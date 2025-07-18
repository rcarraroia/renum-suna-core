import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { authApi } from '../lib/api-client';

// Ícones (usando Lucide React)
import { 
  LayoutDashboard, 
  Bot, 
  BookOpen, 
  Settings, 
  Menu, 
  LogOut 
} from 'lucide-react';

const Sidebar = () => {
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (path: string) => {
    return router.pathname === path || router.pathname.startsWith(`${path}/`);
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      router.push('/login');
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
    }
  };

  return (
    <div className={`bg-gray-800 text-white ${collapsed ? 'w-16' : 'w-64'} transition-all duration-300 ease-in-out flex flex-col`}>
      <div className="p-4 flex justify-between items-center">
        {!collapsed && (
          <div className="flex items-center">
            <Image
              src="/images/logo-renum.png"
              alt="Logo Renum"
              width={32}
              height={32}
              className="mr-2"
            />
            <h2 className="text-xl font-bold">Renum</h2>
          </div>
        )}
        {collapsed && (
          <div className="mx-auto">
            <Image
              src="/images/logo-renum.png"
              alt="Logo Renum"
              width={24}
              height={24}
            />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      <nav className="mt-5 flex-1">
        <ul>
          <li>
            <Link href="/dashboard" className={`flex items-center p-4 ${isActive('/dashboard') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
              <LayoutDashboard className="h-5 w-5" />
              {!collapsed && <span className="ml-3">Dashboard</span>}
            </Link>
          </li>
          <li>
            <Link href="/agents" className={`flex items-center p-4 ${isActive('/agents') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
              <Bot className="h-5 w-5" />
              {!collapsed && <span className="ml-3">Agentes</span>}
            </Link>
          </li>
          <li>
            <Link href="/knowledge-bases" className={`flex items-center p-4 ${isActive('/knowledge-bases') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
              <BookOpen className="h-5 w-5" />
              {!collapsed && <span className="ml-3">Bases de Conhecimento</span>}
            </Link>
          </li>
          <li>
            <Link href="/settings" className={`flex items-center p-4 ${isActive('/settings') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
              <Settings className="h-5 w-5" />
              {!collapsed && <span className="ml-3">Configurações</span>}
            </Link>
          </li>
        </ul>
      </nav>

      <div className="mt-auto mb-4">
        <button
          onClick={handleLogout}
          className="flex items-center p-4 w-full text-left hover:bg-gray-700 rounded-md"
        >
          <LogOut className="h-5 w-5" />
          {!collapsed && <span className="ml-3">Sair</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;