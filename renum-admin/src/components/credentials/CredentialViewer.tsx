import React, { useState } from 'react';
import { Eye, EyeOff, Copy, Check } from 'lucide-react';
import Button from '../ui/Button';
import { useCredentials } from '../../hooks/useCredentials';

interface CredentialViewerProps {
  credentialId: string;
  credentialType: 'api_key' | 'oauth_token' | 'service_account';
  serviceName: string;
}

const CredentialViewer: React.FC<CredentialViewerProps> = ({
  credentialId,
  credentialType,
  serviceName,
}) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const [value, setValue] = useState<string | null>(null);
  const [isCopied, setIsCopied] = useState(false);
  const { revealCredential, isRevealingCredential, error, setError } = useCredentials();

  const handleReveal = async () => {
    if (isRevealed) {
      setValue(null);
      setIsRevealed(false);
      return;
    }

    try {
      const revealedValue = await revealCredential(credentialId);
      setValue(revealedValue);
      setIsRevealed(true);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleCopy = () => {
    if (!value) return;
    
    navigator.clipboard.writeText(value).then(
      () => {
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
      },
      () => {
        setError('Falha ao copiar para a área de transferência');
      }
    );
  };

  const getMaskedValue = () => {
    if (credentialType === 'api_key') {
      return '••••••••••••••••••••••';
    } else if (credentialType === 'oauth_token') {
      return '••••••••••••••••••••••••••••••••••••••••';
    } else {
      return '{ "type": "service_account", ... }';
    }
  };

  const formatValue = (value: string) => {
    if (credentialType === 'service_account') {
      try {
        const jsonObj = JSON.parse(value);
        return JSON.stringify(jsonObj, null, 2);
      } catch (e) {
        return value;
      }
    }
    return value;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Credencial: {serviceName}
        </h3>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReveal}
            isLoading={isRevealingCredential}
          >
            {isRevealed ? (
              <>
                <EyeOff className="h-4 w-4 mr-2" /> Ocultar
              </>
            ) : (
              <>
                <Eye className="h-4 w-4 mr-2" /> Revelar
              </>
            )}
          </Button>
          {isRevealed && value && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              disabled={isCopied}
            >
              {isCopied ? (
                <>
                  <Check className="h-4 w-4 mr-2" /> Copiado
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" /> Copiar
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
        {isRevealed && value ? (
          <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
            {formatValue(value)}
          </pre>
        ) : (
          <div className="text-sm text-gray-500 font-mono">{getMaskedValue()}</div>
        )}
      </div>

      <p className="text-xs text-gray-500">
        {isRevealed
          ? 'Esta credencial está visível temporariamente. Feche esta janela ou clique em "Ocultar" quando terminar.'
          : 'Por segurança, o valor da credencial está oculto. Clique em "Revelar" para visualizar.'}
      </p>
    </div>
  );
};

export default CredentialViewer;