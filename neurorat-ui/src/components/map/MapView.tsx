import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import styled from 'styled-components';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Box, Text, Badge, Heading, Flex, useColorModeValue, Select, Button, HStack, VStack } from '@chakra-ui/react';
import { ZondConnectionStatus, ZondInfo } from '../../types';

// Перезаписываем стандартные маркеры Leaflet
// @ts-ignore - игнорируем ошибку типизации для _getIconUrl
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Пропсы компонента
interface MapViewProps {
  zonds: ZondInfo[];
  center?: [number, number];
  zoom?: number;
  height?: string;
}

interface MapWrapperProps {
  $height: string;
}

// Стилизованные компоненты
const MapWrapper = styled.div<MapWrapperProps>`
  height: ${props => props.$height};
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const ControlsWrapper = styled.div`
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 10px;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const FilterButton = styled(Button)`
  margin: 0 5px;
  font-size: 12px;
`;

// Функция для определения цвета маркера зонда на основе статуса
const getMarkerColor = (status: ZondConnectionStatus): string => {
  switch (status) {
    case ZondConnectionStatus.ONLINE:
      return 'green';
    case ZondConnectionStatus.OFFLINE:
      return 'gray';
    case ZondConnectionStatus.CONNECTING:
      return 'blue';
    case ZondConnectionStatus.ERROR:
      return 'red';
    case ZondConnectionStatus.COMPROMISED:
      return 'orange';
    default:
      return 'gray';
  }
};

// Функция для перевода статуса
const translateStatus = (status: ZondConnectionStatus): string => {
  switch (status) {
    case ZondConnectionStatus.ONLINE:
      return 'Онлайн';
    case ZondConnectionStatus.OFFLINE:
      return 'Оффлайн';
    case ZondConnectionStatus.CONNECTING:
      return 'Подключение';
    case ZondConnectionStatus.ERROR:
      return 'Ошибка';
    case ZondConnectionStatus.COMPROMISED:
      return 'Скомпрометирован';
    default:
      return 'Неизвестно';
  }
};

// Создаем кастомный маркер
const createMarkerIcon = (status: ZondConnectionStatus) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${getMarkerColor(status)};
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 2px solid white;
      box-shadow: 0 0 4px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Компонент для центрирования карты
function SetViewOnChange({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

const MapView: React.FC<MapViewProps> = ({ zonds, center = [55.7558, 37.6173], zoom = 4, height = '600px' }) => {
  const [activeStatusFilter, setActiveStatusFilter] = useState<ZondConnectionStatus | null>(null);
  
  // Фильтруем зонды по статусу
  const filteredZonds = useMemo(() => {
    if (!activeStatusFilter) return zonds;
    return zonds.filter(zond => zond.status === activeStatusFilter);
  }, [zonds, activeStatusFilter]);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');

  return (
    <Box position="relative">
      <MapWrapper $height={height}>
        <MapContainer
          center={center}
          zoom={zoom}
          style={{ height: '100%', width: '100%' }}
          attributionControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          <SetViewOnChange center={center} zoom={zoom} />
          
          {filteredZonds.map((zond) => {
            // Здесь в реальном приложении координаты должны приходить из данных зонда
            // Для демонстрации генерируем случайные точки вокруг центра
            const lat = center[0] + (Math.random() - 0.5) * 10;
            const lng = center[1] + (Math.random() - 0.5) * 20;
            
            return (
              <Marker
                key={zond.id}
                position={[lat, lng]}
                icon={createMarkerIcon(zond.status)}
              >
                <Popup>
                  <VStack align="start" spacing={1} p={1} bg={bgColor} color={textColor}>
                    <Heading size="sm">{zond.name}</Heading>
                    <Badge colorScheme={getMarkerColor(zond.status) === 'gray' ? 'gray' : getMarkerColor(zond.status)}>
                      {translateStatus(zond.status)}
                    </Badge>
                    <Text fontSize="xs">IP: {zond.ipAddress}</Text>
                    {zond.location && <Text fontSize="xs">Местоположение: {zond.location}</Text>}
                    <Text fontSize="xs">ОС: {zond.os}</Text>
                    <Text fontSize="xs">Последняя активность: {new Date(zond.lastSeen).toLocaleString('ru-RU')}</Text>
                  </VStack>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </MapWrapper>
      
      <ControlsWrapper>
        <VStack spacing={2} align="stretch">
          <Text fontSize="sm" fontWeight="bold">Фильтр по статусу:</Text>
          <HStack>
            <FilterButton 
              size="xs" 
              colorScheme={activeStatusFilter === null ? 'blue' : 'gray'}
              onClick={() => setActiveStatusFilter(null)}
            >
              Все
            </FilterButton>
            <FilterButton 
              size="xs" 
              colorScheme={activeStatusFilter === ZondConnectionStatus.ONLINE ? 'green' : 'gray'}
              onClick={() => setActiveStatusFilter(ZondConnectionStatus.ONLINE)}
            >
              Онлайн
            </FilterButton>
            <FilterButton 
              size="xs" 
              colorScheme={activeStatusFilter === ZondConnectionStatus.OFFLINE ? 'gray' : 'gray'}
              onClick={() => setActiveStatusFilter(ZondConnectionStatus.OFFLINE)}
            >
              Оффлайн
            </FilterButton>
            <FilterButton 
              size="xs" 
              colorScheme={activeStatusFilter === ZondConnectionStatus.ERROR ? 'red' : 'gray'}
              onClick={() => setActiveStatusFilter(ZondConnectionStatus.ERROR)}
            >
              Ошибка
            </FilterButton>
          </HStack>
        </VStack>
      </ControlsWrapper>
    </Box>
  );
};

export default MapView; 