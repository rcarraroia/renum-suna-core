import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 py-4 px-6">
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          &copy; {new Date().getFullYear()} Renum Admin. Todos os direitos reservados.
        </div>
        <div className="text-sm text-gray-500">
          Versão 1.0.0
        </div>
      </div>
    </footer>
  );
};

export default Footer;