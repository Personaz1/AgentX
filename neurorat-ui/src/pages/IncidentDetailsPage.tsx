import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { 
  Incident, 
  IncidentStatus, 
  IncidentSeverity, 
  IncidentType,
  IncidentComment,
  IncidentAction
} from '../types';

// Styled Components
const Container = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
`;

const TitleArea = styled.div`
  flex: 1;
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: ${props => props.theme.colors.text.primary};
`;

const IncidentId = styled.div`
  font-size: 14px;
  color: ${props => props.theme.colors.text.secondary};
  margin-bottom: 8px;
`;

const BadgesContainer = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
`;

const SeverityBadge = styled.span<{ severity: IncidentSeverity }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  
  ${props => {
    switch(props.severity) {
      case IncidentSeverity.LOW:
        return `
          background-color: rgba(52, 211, 153, 0.2);
          color: #10B981;
        `;
      case IncidentSeverity.MEDIUM:
        return `
          background-color: rgba(250, 204, 21, 0.2);
          color: #EAB308;
        `;
      case IncidentSeverity.HIGH:
        return `
          background-color: rgba(251, 146, 60, 0.2);
          color: #F97316;
        `;
      case IncidentSeverity.CRITICAL:
        return `
          background-color: rgba(239, 68, 68, 0.2);
          color: #EF4444;
        `;
      default:
        return '';
    }
  }}
`;

const StatusBadge = styled.span<{ status: IncidentStatus }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  
  ${props => {
    switch(props.status) {
      case IncidentStatus.NEW:
        return `
          background-color: rgba(99, 102, 241, 0.2);
          color: #6366F1;
        `;
      case IncidentStatus.INVESTIGATING:
        return `
          background-color: rgba(251, 146, 60, 0.2);
          color: #F97316;
        `;
      case IncidentStatus.MITIGATING:
        return `
          background-color: rgba(14, 165, 233, 0.2);
          color: #0EA5E9;
        `;
      case IncidentStatus.RESOLVED:
        return `
          background-color: rgba(52, 211, 153, 0.2);
          color: #10B981;
        `;
      case IncidentStatus.CLOSED:
        return `
          background-color: rgba(107, 114, 128, 0.2);
          color: #6B7280;
        `;
      default:
        return '';
    }
  }}
`;

const TypeBadge = styled.span`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  background-color: rgba(99, 102, 241, 0.1);
  color: ${props => props.theme.colors.text.primary};
`;

const TagsContainer = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
`;

const Tag = styled.span`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 16px;
  font-size: 12px;
  background: ${props => props.theme.colors.background.tertiary};
  color: ${props => props.theme.colors.text.secondary};
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  
  ${props => {
    switch(props.variant) {
      case 'primary':
        return `
          background: ${props.theme.colors.primary};
          color: white;
        `;
      case 'danger':
        return `
          background: #EF4444;
          color: white;
        `;
      case 'secondary':
      default:
        return `
          background: ${props.theme.colors.background.tertiary};
          color: ${props.theme.colors.text.primary};
          border: 1px solid ${props.theme.colors.border.primary};
        `;
    }
  }}
  
  &:hover {
    opacity: 0.9;
  }
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const Section = styled.div`
  background: ${props => props.theme.colors.background.secondary};
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: ${props => props.theme.colors.text.primary};
`;

const Description = styled.p`
  margin-bottom: 16px;
  line-height: 1.6;
  color: ${props => props.theme.colors.text.primary};
  white-space: pre-line;
`;

const DetailsList = styled.dl`
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px 16px;
`;

const DetailTerm = styled.dt`
  font-weight: 500;
  color: ${props => props.theme.colors.text.secondary};
`;

const DetailValue = styled.dd`
  margin: 0;
  color: ${props => props.theme.colors.text.primary};
`;

const Timeline = styled.div`
  margin-top: 24px;
`;

const TimelineItem = styled.div`
  position: relative;
  padding-left: 28px;
  padding-bottom: 20px;
  border-left: 2px solid ${props => props.theme.colors.border.primary};
  margin-left: 8px;
  
  &:last-child {
    border-left: none;
  }
  
  &::before {
    content: '';
    position: absolute;
    left: -8px;
    top: 0;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: ${props => props.theme.colors.primary};
  }
`;

const TimelineDate = styled.div`
  font-size: 12px;
  color: ${props => props.theme.colors.text.secondary};
  margin-bottom: 4px;
`;

const TimelineTitle = styled.div`
  font-weight: 500;
  margin-bottom: 4px;
  color: ${props => props.theme.colors.text.primary};
`;

const TimelineDescription = styled.div`
  font-size: 14px;
  color: ${props => props.theme.colors.text.secondary};
`;

const CommentsSection = styled.div`
  margin-top: 24px;
`;

const CommentItem = styled.div`
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid ${props => props.theme.colors.border.primary};
  
  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }
`;

const CommentHeader = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
`;

const CommentAuthor = styled.div`
  font-weight: 500;
  color: ${props => props.theme.colors.text.primary};
`;

const CommentDate = styled.div`
  font-size: 12px;
  color: ${props => props.theme.colors.text.secondary};
`;

const CommentText = styled.p`
  margin: 0;
  line-height: 1.5;
  color: ${props => props.theme.colors.text.primary};
`;

const CommentForm = styled.form`
  margin-top: 16px;
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.colors.border.primary};
  background: ${props => props.theme.colors.background.tertiary};
  color: ${props => props.theme.colors.text.primary};
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const SystemBox = styled.div<{ type: 'affected' | 'normal' }>`
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  ${props => props.type === 'affected' ? `
    background-color: rgba(239, 68, 68, 0.1);
    border-left: 3px solid #EF4444;
  ` : `
    background: ${props.theme.colors.background.tertiary};
  `
`;

const PageContainer = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const BackButton = styled.button`
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  background: ${props => props.theme.colors.background.tertiary};
  color: ${props => props.theme.colors.text.primary};
  border: 1px solid ${props => props.theme.colors.border.primary};
  
  &:hover {
    opacity: 0.9;
  }
`;

const MainContent = styled.div`
  display: flex;
  gap: 24px;
  
  @media (max-width: 1024px) {
    flex-direction: column;
  }
`;

const LeftColumn = styled.div`
  flex: 2;
`;

const RightColumn = styled.div`
  flex: 1;
`;

const Card = styled.div`
  background: ${props => props.theme.colors.background.secondary};
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
`;

const MetaItem = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
`;

const TagList = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const AttachmentList = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const Attachment = styled.a`
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: ${props => props.theme.colors.text.primary};
  
  &:hover {
    text-decoration: underline;
  }
`;

const EventList = styled.div`
  margin-bottom: 20px;
`;

const EventItem = styled.div`
  margin-bottom: 8px;
`;

const EventTimestamp = styled.span`
  font-size: 12px;
  color: ${props => props.theme.colors.text.secondary};
`;

const EventMessage = styled.span`
  font-size: 14px;
  color: ${props => props.theme.colors.text.primary};
`;

const EventUser = styled.span`
  font-weight: 500;
  color: ${props => props.theme.colors.text.primary};
`;

const Textarea = styled.textarea`
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.colors.border.primary};
  background: ${props => props.theme.colors.background.tertiary};
  color: ${props => props.theme.colors.text.primary};
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Actions = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const IncidentDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [updating, setUpdating] = useState(false);
  const [commentText, setCommentText] = useState('');

  useEffect(() => {
    // Fetch incident data
    // This is a placeholder and should be replaced with actual data fetching logic
    setIncident({
      id: '1',
      title: 'Incident Title',
      status: IncidentStatus.NEW,
      severity: IncidentSeverity.LOW,
      type: IncidentType.UNSPECIFIED,
      description: 'This is a sample incident description.',
      detectedDate: new Date(),
      assignedTo: 'John Doe',
      affectedSystems: ['System A', 'System B'],
      ipAddresses: ['192.168.1.1', '10.0.0.2'],
      indicators: ['Indicator 1', 'Indicator 2'],
      attachments: [
        { id: '1', name: 'Attachment 1', url: 'https://example.com/attachment1.pdf' },
        { id: '2', name: 'Attachment 2', url: 'https://example.com/attachment2.pdf' }
      ],
      events: [
        { id: '1', timestamp: new Date(), user: 'John Doe', message: 'Incident started' },
        { id: '2', timestamp: new Date(), user: 'Jane Doe', message: 'Investigation started' }
      ]
    });
  }, []);

  const handleStatusChange = async (newStatus: IncidentStatus) => {
    setUpdating(true);
    try {
      // Update incident status
      // This is a placeholder and should be replaced with actual API call
      setIncident(prevIncident => ({ ...prevIncident!, status: newStatus }));
    } catch (error) {
      console.error('Error updating incident status:', error);
    } finally {
      setUpdating(false);
    }
  };

  const handleAddComment = async () => {
    setUpdating(true);
    try {
      // Add comment
      // This is a placeholder and should be replaced with actual API call
      setCommentText('');
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setUpdating(false);
    }
  };

  if (!incident) {
    return <div>Loading...</div>;
  }

  return (
    <PageContainer>
      <BackButton onClick={() => navigate('/incidents')}>← Вернуться к списку инцидентов</BackButton>
      
      <Header>
        <div>
          <Title>{incident.title}</Title>
          <div style={{ marginTop: '12px' }}>
            <StatusBadge status={incident.status}>
              {getStatusText(incident.status)}
            </StatusBadge>
            <SeverityBadge severity={incident.severity}>
              {getSeverityText(incident.severity)}
            </SeverityBadge>
            <TypeBadge>{getTypeText(incident.type)}</TypeBadge>
          </div>
        </div>
        
        <Actions>
          {incident.status === IncidentStatus.NEW && (
            <Button 
              variant="primary" 
              onClick={() => handleStatusChange(IncidentStatus.INVESTIGATING)}
              disabled={updating}
            >
              Начать расследование
            </Button>
          )}
          
          {incident.status === IncidentStatus.INVESTIGATING && (
            <Button 
              variant="primary" 
              onClick={() => handleStatusChange(IncidentStatus.RESOLVED)}
              disabled={updating}
            >
              Отметить как решенный
            </Button>
          )}
          
          {incident.status === IncidentStatus.RESOLVED && (
            <Button 
              variant="primary" 
              onClick={() => handleStatusChange(IncidentStatus.CLOSED)}
              disabled={updating}
            >
              Закрыть инцидент
            </Button>
          )}
          
          {incident.status !== IncidentStatus.NEW && incident.status !== IncidentStatus.CLOSED && (
            <Button 
              variant="warning" 
              onClick={() => handleStatusChange(IncidentStatus.NEW)}
              disabled={updating}
            >
              Вернуть статус "Новый"
            </Button>
          )}
          
          <Button variant="secondary">Экспорт в PDF</Button>
        </Actions>
      </Header>
      
      <MainContent>
        <LeftColumn>
          <Card>
            <SectionTitle>Описание</SectionTitle>
            <Description>{incident.description}</Description>
          </Card>
          
          <Card>
            <SectionTitle>Хронология событий</SectionTitle>
            <EventList>
              {incident.events.map(event => (
                <EventItem key={event.id}>
                  <EventTimestamp>{formatEventDate(event.timestamp)}</EventTimestamp>
                  <EventMessage>
                    {event.user && <EventUser>{event.user}: </EventUser>}
                    {event.message}
                  </EventMessage>
                </EventItem>
              ))}
            </EventList>
            
            <SectionTitle style={{ marginTop: '20px' }}>Добавить комментарий</SectionTitle>
            <Textarea 
              placeholder="Введите комментарий..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
            />
            <Button 
              variant="primary" 
              onClick={handleAddComment}
              disabled={!commentText.trim() || updating}
            >
              Добавить
            </Button>
          </Card>
        </LeftColumn>
        
        <RightColumn>
          <Card>
            <SectionTitle>Информация</SectionTitle>
            
            <MetaItem>
              <span>ID инцидента</span>
              <span>{incident.id}</span>
            </MetaItem>
            
            <MetaItem>
              <span>Обнаружен</span>
              <span>{formatDate(incident.detectedDate)}</span>
            </MetaItem>
            
            {incident.assignedTo && (
              <MetaItem>
                <span>Назначен</span>
                <span>{incident.assignedTo}</span>
              </MetaItem>
            )}
          </Card>
          
          <Card>
            <SectionTitle>Затронутые системы</SectionTitle>
            <TagList>
              {incident.affectedSystems.map((system, index) => (
                <Tag key={index}>{system}</Tag>
              ))}
            </TagList>
          </Card>
          
          {incident.ipAddresses && incident.ipAddresses.length > 0 && (
            <Card>
              <SectionTitle>IP-адреса</SectionTitle>
              <TagList>
                {incident.ipAddresses.map((ip, index) => (
                  <Tag key={index}>{ip}</Tag>
                ))}
              </TagList>
            </Card>
          )}
          
          {incident.indicators && incident.indicators.length > 0 && (
            <Card>
              <SectionTitle>Индикаторы компрометации</SectionTitle>
              <TagList>
                {incident.indicators.map((indicator, index) => (
                  <Tag key={index}>{indicator}</Tag>
                ))}
              </TagList>
            </Card>
          )}
          
          {incident.attachments && incident.attachments.length > 0 && (
            <Card>
              <SectionTitle>Вложения</SectionTitle>
              <AttachmentList>
                {incident.attachments.map(attachment => (
                  <Attachment 
                    key={attachment.id}
                    href={attachment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    📎 <span>{attachment.name}</span>
                  </Attachment>
                ))}
              </AttachmentList>
            </Card>
          )}
        </RightColumn>
      </MainContent>
    </PageContainer>
  );
};

export default IncidentDetailsPage;