import React from 'react';
import { useForm } from 'react-hook-form';
import { TypewriterPhraseFormData } from '../../types/homepage';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

interface PhraseFormProps {
  defaultValues?: Partial<TypewriterPhraseFormData>;
  onSubmit: (data: TypewriterPhraseFormData) => void;
  isSubmitting: boolean;
  isEditMode?: boolean;
}

const PhraseForm: React.FC<PhraseFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  isEditMode = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TypewriterPhraseFormData>({
    defaultValues: defaultValues || {
      text: '',
      display_order: 0,
      is_active: true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 gap-6">
        <div>
          <label
            htmlFor="text"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Texto da Frase *
          </label>
          <Input
            id="text"
            {...register('text', { required: 'O texto da frase é obrigatório' })}
            error={errors.text?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            Este texto será exibido com efeito de máquina de escrever na página inicial
          </p>
        </div>

        <div>
          <label
            htmlFor="display_order"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Ordem de Exibição *
          </label>
          <Input
            id="display_order"
            type="number"
            min="0"
            {...register('display_order', {
              required: 'A ordem de exibição é obrigatória',
              valueAsNumber: true,
              min: {
                value: 0,
                message: 'A ordem de exibição deve ser pelo menos 0',
              },
            })}
            error={errors.display_order?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            As frases serão exibidas em ordem crescente
          </p>
        </div>

        <div>
          <label
            htmlFor="is_active"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Status
          </label>
          <Select
            id="is_active"
            {...register('is_active')}
            options={[
              { value: 'true', label: 'Ativo' },
              { value: 'false', label: 'Inativo' },
            ]}
          />
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {isEditMode ? 'Atualizar Frase' : 'Criar Frase'}
        </Button>
      </div>
    </form>
  );
};

export default PhraseForm;