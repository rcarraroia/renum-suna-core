import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  Home,
  Users,
  Building,
  Bot,
  Key,
  CreditCard,
  Settings,
  FileText,
  ChevronDown,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

interface NavItemProps {
  href: string;
  icon: React.ReactNode;
  text: string;
  active?: boolean;
  hasSubmenu?: boolean;
  open?: boolean;
  onClick?: () => void;
}

const NavItem: React.FC<NavItemProps> = ({
  href,
  icon,
  text,
  active,
  hasSubmenu,
  open,
  onClick,
}) => {
  return (
    <Link href={href}>
      <a
        className={`flex items-center px-4 py-3 text-sm font-medium rounded-md ${
          active
            ? 'bg-primary-700 text-white'
            : 'text-gray-300 hover:bg-primary-800 hover:text-white'
        }`}
        onClick={onClick}
      >
        <span className="mr-3">{icon}</span>
        <span className="flex-1">{text}</span>
        {hasSubmenu && (
          <span className="ml-2">
            {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </span>
        )}
      </a>
    </Link>
  );
};

const Sidebar: React.FC = () => {
  const router = useRouter();
  const { logout } = useAuth();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isActive = (path: string) => router.pathname === path;
  const isActiveGroup = (paths: string[]) =>
    paths.some((path) => router.pathname.startsWith(path));

  return (
    <div className="bg-primary-900 text-white w-64 flex-shrink-0 hidden md:block">
      <div className="h-16 flex items-center px-6">
        <h1 className="text-xl font-bold">Renum Admin</h1>
      </div>
      
      <div className="px-3 py-4 space-y-1">
        <NavItem
          href="/"
          icon={<Home size={20} />}
          text="Dashboard"
          active={isActive('/')}
        />
        
        <NavItem
          href="/clients"
          icon={<Building size={20} />}
          text="Clientes"
          active={isActiveGroup(['/clients'])}
        />
        
        <NavItem
          href="/users"
          icon={<Users size={20} />}
          text="Usuários"
          active={isActiveGroup(['/users'])}
        />
        
        <NavItem
          href="/agents"
          icon={<Bot size={20} />}
          text="Agentes"
          active={isActiveGroup(['/agents'])}
        />
        
        <NavItem
          href="/credentials"
          icon={<Key size={20} />}
          text="Credenciais"
          active={isActiveGroup(['/credentials'])}
        />
        
        <NavItem
          href="/billing"
          icon={<CreditCard size={20} />}
          text="Faturamento"
          active={isActiveGroup(['/billing'])}
        />
        
        <NavItem
          href="/settings"
          icon={<Settings size={20} />}
          text="Configurações"
          active={isActiveGroup(['/settings'])}
          hasSubmenu={true}
          open={settingsOpen}
          onClick={() => setSettingsOpen(!settingsOpen)}
        />
        
        {settingsOpen && (
          <div className="pl-10 space-y-1">
            <NavItem
              href="/settings"
              icon={<Settings size={16} />}
              text="Geral"
              active={isActive('/settings')}
            />
            <NavItem
              href="/settings/security"
              icon={<Settings size={16} />}
              text="Segurança"
              active={isActive('/settings/security')}
            />
            <NavItem
              href="/settings/integrations"
              icon={<Settings size={16} />}
              text="Integrações"
              active={isActive('/settings/integrations')}
            />
          </div>
        )}
        
        <NavItem
          href="/audit"
          icon={<FileText size={20} />}
          text="Auditoria"
          active={isActiveGroup(['/audit'])}
        />
        
        <div className="pt-4 mt-4 border-t border-primary-800">
          <button
            onClick={logout}
            className="flex items-center px-4 py-3 text-sm font-medium rounded-md text-gray-300 hover:bg-primary-800 hover:text-white w-full"
          >
            <LogOut size={20} className="mr-3" />
            <span>Sair</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;