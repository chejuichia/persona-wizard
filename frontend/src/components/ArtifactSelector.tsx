"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, FileText, Image, Mic, Trash2, Clock, HardDrive } from 'lucide-react';

interface Artifact {
  id: string;
  type: 'audio' | 'text' | 'image';
  name: string;
  created_at: string;
  file_path: string;
  metadata: any;
  size?: number;
  duration?: number;
  dimensions?: number[];
}

interface ArtifactSelectorProps {
  onSelect: (artifact: Artifact) => void;
  selectedArtifact?: Artifact | null;
  artifactType?: 'audio' | 'text' | 'image' | 'all';
  className?: string;
}

export default function ArtifactSelector({ 
  onSelect, 
  selectedArtifact, 
  artifactType = 'all',
  className = '' 
}: ArtifactSelectorProps) {
  const [artifacts, setArtifacts] = useState<{ [key: string]: Artifact[] }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const fetchArtifacts = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/artifacts/');
      
      if (!response.ok) {
        throw new Error('Failed to fetch artifacts');
      }
      
      const data = await response.json();
      setArtifacts(data.artifacts);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch artifacts');
      console.error('Error fetching artifacts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (artifact: Artifact) => {
    try {
      const response = await fetch(`http://localhost:8000/artifacts/${artifact.type}/${artifact.id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete artifact');
      }
      
      // Refresh artifacts list
      await fetchArtifacts();
    } catch (err) {
      console.error('Error deleting artifact:', err);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getArtifactIcon = (type: string) => {
    switch (type) {
      case 'audio':
        return <Mic className="h-4 w-4" />;
      case 'text':
        return <FileText className="h-4 w-4" />;
      case 'image':
        return <Image className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const renderArtifactCard = (artifact: Artifact) => (
    <Card 
      key={artifact.id}
      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
        selectedArtifact?.id === artifact.id 
          ? 'ring-2 ring-blue-500 bg-blue-50' 
          : 'hover:bg-gray-50'
      }`}
      onClick={() => onSelect(artifact)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getArtifactIcon(artifact.type)}
            <CardTitle className="text-sm font-medium">{artifact.name}</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(artifact);
            }}
            className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <Clock className="h-3 w-3" />
            <span>{formatDate(artifact.created_at)}</span>
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <HardDrive className="h-3 w-3" />
            <span>{formatFileSize(artifact.size)}</span>
          </div>
          
          {artifact.duration && (
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <Play className="h-3 w-3" />
              <span>{formatDuration(artifact.duration)}</span>
            </div>
          )}
          
          {artifact.dimensions && (
            <div className="text-xs text-gray-500">
              {artifact.dimensions[0]} × {artifact.dimensions[1]} px
            </div>
          )}
          
          <Badge variant="secondary" className="text-xs">
            {artifact.type.toUpperCase()}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-500">Loading artifacts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="text-center py-8">
          <p className="text-red-500 text-sm">{error}</p>
          <Button 
            onClick={fetchArtifacts} 
            variant="outline" 
            size="sm" 
            className="mt-2"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const totalArtifacts = Object.values(artifacts).reduce((sum, list) => sum + list.length, 0);

  if (totalArtifacts === 0) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="text-center py-8">
          <p className="text-gray-500 text-sm">No previous artifacts found</p>
          <p className="text-xs text-gray-400 mt-1">
            Upload some content to see it here for reuse
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Previous Artifacts</h3>
        <Badge variant="outline" className="text-xs">
          {totalArtifacts} total
        </Badge>
      </div>

      {artifactType === 'all' ? (
        <Tabs defaultValue="audio" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="audio" className="flex items-center space-x-1">
              <Mic className="h-3 w-3" />
              <span>Audio ({artifacts.audio?.length || 0})</span>
            </TabsTrigger>
            <TabsTrigger value="text" className="flex items-center space-x-1">
              <FileText className="h-3 w-3" />
              <span>Text ({artifacts.text?.length || 0})</span>
            </TabsTrigger>
            <TabsTrigger value="image" className="flex items-center space-x-1">
              <Image className="h-3 w-3" />
              <span>Images ({artifacts.image?.length || 0})</span>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="audio" className="space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {artifacts.audio?.map(renderArtifactCard) || []}
            </div>
          </TabsContent>
          
          <TabsContent value="text" className="space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {artifacts.text?.map(renderArtifactCard) || []}
            </div>
          </TabsContent>
          
          <TabsContent value="image" className="space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {artifacts.image?.map(renderArtifactCard) || []}
            </div>
          </TabsContent>
        </Tabs>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {artifacts[artifactType]?.map(renderArtifactCard) || []}
        </div>
      )}
    </div>
  );
}
