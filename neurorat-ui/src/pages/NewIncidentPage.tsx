import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

// Определяем типы
type IncidentStatus = 'new' | 'investigating' | 'resolved' | 'closed';
type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low';
type IncidentType = 'intrusion' | 'malware' | 'dos' | 'unauthorized_access' | 'data_breach' | 'other';

interface NewIncidentData {
  title: string;
  description: string;
  severity: IncidentSeverity;
  type: IncidentType;
  affectedSystems: string[];
  ipAddresses: string[];
  indicators: string[];
}

// Стилизованные компоненты
const PageContainer = styled.div`
  padding: 24px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #F8F8F2;
  margin: 0;
`;

const FormSection = styled.div`
  background-color: #282A36;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #F8F8F2;
  margin: 0 0 16px 0;
  border-bottom: 1px solid #44475A;
  padding-bottom: 8px;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #F8F8F2;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  background-color: #1E1E2E;
  border: 1px solid #44475A;
  border-radius: 6px;
  color: #F8F8F2;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }
`;

const Textarea = styled.textarea`
  width: 100%;
  min-height: 120px;
  padding: 12px;
  background-color: #1E1E2E;
  border: 1px solid #44475A;
  border-radius: 6px;
  color: #F8F8F2;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 12px;
  background-color: #1E1E2E;
  border: 1px solid #44475A;
  border-radius: 6px;
  color: #F8F8F2;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }
`;

const TagsInputContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  min-height: 46px;
  background-color: #1E1E2E;
  border: 1px solid #44475A;
  border-radius: 6px;
`;

const TagItem = styled.div`
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background-color: #44475A;
  border-radius: 4px;
  color: #F8F8F2;
  font-size: 13px;
`;

const TagText = styled.span`
  margin-right: 6px;
`;

const RemoveTagButton = styled.button`
  background: none;
  border: none;
  color: #F8F8F2;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  display: flex;
  align-items: center;
  
  &:hover {
    color: #FF5555;
  }
`;

const TagInput = styled.input`
  flex: 1;
  min-width: 120px;
  background: none;
  border: none;
  color: #F8F8F2;
  outline: none;
  font-size: 14px;
  padding: 4px;
`;

const ButtonsContainer = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 24px;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  
  background-color: ${props => 
    props.variant === 'primary' ? '#BD93F9' : 'transparent'};
  
  color: ${props => 
    props.variant === 'primary' ? '#282A36' : '#F8F8F2'};
    
  border: ${props => 
    props.variant === 'primary' ? 'none' : '1px solid #44475A'};
    
  &:hover {
    background-color: ${props => 
      props.variant === 'primary' ? '#A580FF' : '#44475A'};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  color: #FF5555;
  font-size: 14px;
  margin-top: 4px;
`;

const NewIncidentPage: React.FC = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Состояние формы
  const [formData, setFormData] = useState<NewIncidentData>({
    title: '',
    description: '',
    severity: 'medium',
    type: 'other',
    affectedSystems: [],
    ipAddresses: [],
    indicators: []
  });
  
  // Состояние для временных тегов
  const [systemInput, setSystemInput] = useState('');
  const [ipInput, setIpInput] = useState('');
  const [indicatorInput, setIndicatorInput] = useState('');
  
  // Обработчики изменения полей формы
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  // Обработчики для тегов
  const handleAddSystem = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && systemInput.trim()) {
      e.preventDefault();
      setFormData(prev => ({
        ...prev,
        affectedSystems: [...prev.affectedSystems, systemInput.trim()]
      }));
      setSystemInput('');
    }
  };
  
  const handleRemoveSystem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      affectedSystems: prev.affectedSystems.filter((_, i) => i !== index)
    }));
  };
  
  const handleAddIP = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && ipInput.trim()) {
      e.preventDefault();
      setFormData(prev => ({
        ...prev,
        ipAddresses: [...prev.ipAddresses, ipInput.trim()]
      }));
      setIpInput('');
    }
  };
  
  const handleRemoveIP = (index: number) => {
    setFormData(prev => ({
      ...prev,
      ipAddresses: prev.ipAddresses.filter((_, i) => i !== index)
    }));
  };
  
  const handleAddIndicator = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && indicatorInput.trim()) {
      e.preventDefault();
      setFormData(prev => ({
        ...prev,
        indicators: [...prev.indicators, indicatorInput.trim()]
      }));
      setIndicatorInput('');
    }
  };
  
  const handleRemoveIndicator = (index: number) => {
    setFormData(prev => ({
      ...prev,
      indicators: prev.indicators.filter((_, i) => i !== index)
    }));
  };
  
  // Проверка формы перед отправкой
  const validateForm = (): boolean => {
    if (!formData.title.trim()) {
      setError('Необходимо указать название инцидента');
      return false;
    }
    
    if (!formData.description.trim()) {
      setError('Необходимо добавить описание инцидента');
      return false;
    }
    
    if (formData.affectedSystems.length === 0) {
      setError('Необходимо указать хотя бы одну затронутую систему');
      return false;
    }
    
    setError(null);
    return true;
  };
  
  // Обработчик отправки формы
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    
    // Здесь в реальном приложении был бы запрос к API
    // Имитируем успешное создание инцидента
    setTimeout(() => {
      setIsSubmitting(false);
      navigate('/incidents'); // Переход на страницу со списком инцидентов
    }, 1000);
  };
  
  const handleCancel = () => {
    navigate('/incidents');
  };
  
  return (
    <PageContainer>
      <Header>
        <Title>Новый инцидент</Title>
      </Header>
      
      <form onSubmit={handleSubmit}>
        <FormSection>
          <SectionTitle>Основная информация</SectionTitle>
          
          <FormGroup>
            <Label htmlFor="title">Название инцидента *</Label>
            <Input
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="Введите название инцидента"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="description">Описание *</Label>
            <Textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Подробно опишите инцидент, его признаки и возможные причины"
              required
            />
          </FormGroup>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <FormGroup>
              <Label htmlFor="severity">Важность *</Label>
              <Select
                id="severity"
                name="severity"
                value={formData.severity}
                onChange={handleInputChange}
                required
              >
                <option value="low">Низкая</option>
                <option value="medium">Средняя</option>
                <option value="high">Высокая</option>
                <option value="critical">Критическая</option>
              </Select>
            </FormGroup>
            
            <FormGroup>
              <Label htmlFor="type">Тип инцидента *</Label>
              <Select
                id="type"
                name="type"
                value={formData.type}
                onChange={handleInputChange}
                required
              >
                <option value="intrusion">Вторжение</option>
                <option value="malware">Вредоносное ПО</option>
                <option value="dos">DoS-атака</option>
                <option value="unauthorized_access">Несанкционированный доступ</option>
                <option value="data_breach">Утечка данных</option>
                <option value="other">Другое</option>
              </Select>
            </FormGroup>
          </div>
        </FormSection>
        
        <FormSection>
          <SectionTitle>Затронутые системы и индикаторы</SectionTitle>
          
          <FormGroup>
            <Label>Затронутые системы *</Label>
            <TagsInputContainer>
              {formData.affectedSystems.map((system, index) => (
                <TagItem key={index}>
                  <TagText>{system}</TagText>
                  <RemoveTagButton 
                    type="button" 
                    onClick={() => handleRemoveSystem(index)}
                  >
                    ×
                  </RemoveTagButton>
                </TagItem>
              ))}
              <TagInput
                value={systemInput}
                onChange={(e) => setSystemInput(e.target.value)}
                onKeyDown={handleAddSystem}
                placeholder={formData.affectedSystems.length ? "" : "Введите имя системы и нажмите Enter"}
              />
            </TagsInputContainer>
          </FormGroup>
          
          <FormGroup>
            <Label>IP-адреса</Label>
            <TagsInputContainer>
              {formData.ipAddresses.map((ip, index) => (
                <TagItem key={index}>
                  <TagText>{ip}</TagText>
                  <RemoveTagButton 
                    type="button" 
                    onClick={() => handleRemoveIP(index)}
                  >
                    ×
                  </RemoveTagButton>
                </TagItem>
              ))}
              <TagInput
                value={ipInput}
                onChange={(e) => setIpInput(e.target.value)}
                onKeyDown={handleAddIP}
                placeholder={formData.ipAddresses.length ? "" : "Введите IP-адрес и нажмите Enter"}
              />
            </TagsInputContainer>
          </FormGroup>
          
          <FormGroup>
            <Label>Индикаторы компрометации</Label>
            <TagsInputContainer>
              {formData.indicators.map((indicator, index) => (
                <TagItem key={index}>
                  <TagText>{indicator}</TagText>
                  <RemoveTagButton 
                    type="button" 
                    onClick={() => handleRemoveIndicator(index)}
                  >
                    ×
                  </RemoveTagButton>
                </TagItem>
              ))}
              <TagInput
                value={indicatorInput}
                onChange={(e) => setIndicatorInput(e.target.value)}
                onKeyDown={handleAddIndicator}
                placeholder={formData.indicators.length ? "" : "Введите индикатор и нажмите Enter"}
              />
            </TagsInputContainer>
          </FormGroup>
        </FormSection>
        
        {error && <ErrorMessage>{error}</ErrorMessage>}
        
        <ButtonsContainer>
          <Button type="button" onClick={handleCancel}>
            Отмена
          </Button>
          <Button 
            type="submit" 
            variant="primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Создание...' : 'Создать инцидент'}
          </Button>
        </ButtonsContainer>
      </form>
    </PageContainer>
  );
};

export default NewIncidentPage; 