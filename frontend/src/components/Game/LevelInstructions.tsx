import React, { useState } from 'react';
import { ShieldCheck, BookOpen, Terminal, Compass, CheckCircle2, ChevronRight, HelpCircle, HardDrive } from 'lucide-react';
import { LevelType } from './GameInterface';

interface LevelInstructionsProps {
  level: LevelType;
}

export default function LevelInstructions({ level }: LevelInstructionsProps) {
  const [activeSubTab, setActiveSubTab] = useState<'mission' | 'support'>('mission');

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    return `${mins}m ${remainingSecs > 0 ? remainingSecs + 's' : ''}`;
  };

  const subObjectives = level.scenario?.expected_state?.files_checks || [];

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#050816]/95 select-none font-mono text-xs text-gray-300">
      
      {/* Tabs Selector at the top of the Left column */}
      <div className="flex border-b border-gray-850 bg-gray-950/40 p-1.5 shrink-0">
        <button
          onClick={() => setActiveSubTab('mission')}
          className={`flex-1 py-2 rounded-xl font-bold tracking-wider transition-all flex items-center justify-center space-x-2 ${
            activeSubTab === 'mission'
              ? 'bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/25'
              : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          <Compass className="h-4 w-4" />
          <span>MISSION</span>
        </button>
        <button
          onClick={() => setActiveSubTab('support')}
          className={`flex-1 py-2 rounded-xl font-bold tracking-wider transition-all flex items-center justify-center space-x-2 ${
            activeSubTab === 'support'
              ? 'bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/25'
              : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          <BookOpen className="h-4 w-4" />
          <span>SUPPORT TECHNIQUE</span>
        </button>
      </div>

      {/* Main Column Pane Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        
        {activeSubTab === 'mission' ? (
          <>
            {/* Meta Title block */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-black bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                  Dossier Actif
                </span>
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">INDEX : #{level.level_index + 1}</span>
              </div>
              <h2 className="text-sm font-black text-white leading-snug tracking-wide select-text">{level.title}</h2>
            </div>

            {/* Context & Description */}
            <div className="space-y-2">
              <h3 className="text-[10px] font-black uppercase tracking-widest text-gray-500">Description du Problème</h3>
              <p className="text-xs text-gray-300 leading-relaxed select-text bg-[#03050f]/60 p-4 rounded-xl border border-gray-850/60 shadow-[inset_0_1px_1px_rgba(255,255,255,0.01)]">
                {level.description}
              </p>
            </div>

            {/* Main Objective */}
            <div className="p-4 bg-[#10B981]/5 border border-[#10B981]/15 rounded-xl space-y-2.5">
              <h3 className="text-[10px] font-black uppercase tracking-widest text-[#10B981] flex items-center space-x-1.5">
                <ShieldCheck className="h-4 w-4" />
                <span>Objectif Principal</span>
              </h3>
              <p className="text-xs text-gray-200 select-text leading-relaxed">
                {level.objective}
              </p>
            </div>

            {/* Validation criteria checklists */}
            {subObjectives.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-[10px] font-black uppercase tracking-widest text-gray-500">Critères de validation</h3>
                <div className="space-y-2">
                  {subObjectives.map((check: any, idx: number) => {
                    const targetPath = check.path || "Fichier";
                    const isPerm = check.perms ? ` (Permissions : ${check.perms})` : "";
                    const isContent = check.content_contains ? ` (Doit contenir une directive spécifique)` : "";
                    
                    return (
                      <div key={idx} className="flex items-start space-x-3 p-3 bg-[#03050f]/40 border border-gray-850/50 rounded-xl">
                        <div className="h-5 w-5 rounded-lg border border-gray-800 bg-gray-950 flex items-center justify-center shrink-0 mt-0.5">
                          <span className="text-[9px] font-black text-gray-400">{idx + 1}</span>
                        </div>
                        <div className="text-xs text-gray-300 leading-relaxed select-text">
                          <span className="text-white font-semibold">Vérifier `{targetPath}`</span>{isPerm}{isContent}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            {/* Technical Reference Manual / Wiki Support */}
            <div className="space-y-5 select-text">
              <div className="space-y-1">
                <h3 className="text-[11px] font-black uppercase tracking-widest text-white flex items-center space-x-1.5">
                  <Terminal className="h-4 w-4 text-[#10B981]" />
                  <span>Manuel de Référence Technique</span>
                </h3>
                <p className="text-[10px] text-gray-500 leading-relaxed">Fiches de support technique adaptées aux défis de cette session :</p>
              </div>

              {/* Guide Item 1: Permissions */}
              <div className="p-4 bg-gray-950/40 border border-gray-850/50 rounded-xl space-y-2.5">
                <h4 className="font-bold text-white text-xs flex items-center space-x-1.5">
                  <ChevronRight className="h-3.5 w-3.5 text-[#10B981]" />
                  <span>Gestion des Permissions (chmod)</span>
                </h4>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  En Linux, les permissions régissent les droits d'accès. La commande <code className="text-[#10B981] font-bold">chmod</code> modifie ces droits :
                </p>
                <div className="bg-[#03050f] p-2.5 rounded-lg border border-gray-850 font-mono text-[10px] text-gray-300 space-y-1.5">
                  <p><span className="text-gray-500"># Restreindre l'accès au propriétaire (lecture/écriture)</span></p>
                  <p><span className="text-emerald-400">chmod 600</span> secret.txt</p>
                  <p><span className="text-gray-500"># Donner accès complet propriétaire, lecture/exécution aux autres</span></p>
                  <p><span className="text-emerald-400">chmod 755</span> /var/www/html</p>
                </div>
              </div>

              {/* Guide Item 2: Text editing and Echo redirection */}
              <div className="p-4 bg-gray-950/40 border border-gray-850/50 rounded-xl space-y-2.5">
                <h4 className="font-bold text-white text-xs flex items-center space-x-1.5">
                  <ChevronRight className="h-3.5 w-3.5 text-[#10B981]" />
                  <span>Redirection de Flux et Écriture</span>
                </h4>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  Pour modifier ou créer un fichier de configuration sans éditeur visuel, vous pouvez utiliser les opérateurs d'écriture :
                </p>
                <div className="bg-[#03050f] p-2.5 rounded-lg border border-gray-850 font-mono text-[10px] text-gray-300 space-y-1.5">
                  <p><span className="text-gray-500"># Écraser ou créer le fichier avec un contenu</span></p>
                  <p><span className="text-emerald-400">echo "Options -Indexes" &gt;</span> /etc/apache2/apache2.conf</p>
                  <p><span className="text-gray-500"># Ajouter un contenu à la fin du fichier sans écraser</span></p>
                  <p><span className="text-emerald-400">echo "AllowOverride None" &gt;&gt;</span> /etc/apache2/apache2.conf</p>
                </div>
              </div>

              {/* Guide Item 3: Server Directory Indexing */}
              <div className="p-4 bg-gray-950/40 border border-gray-850/50 rounded-xl space-y-2.5">
                <h4 className="font-bold text-white text-xs flex items-center space-x-1.5">
                  <ChevronRight className="h-3.5 w-3.5 text-[#10B981]" />
                  <span>Désactiver l'indexation de Dossier</span>
                </h4>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  L'affichage d'un dossier web par défaut (autoindex) expose la structure des fichiers. Dans Apache, l'indexation se désactive en spécifiant la directive négative suivante :
                </p>
                <div className="bg-[#03050f] p-2.5 rounded-lg border border-gray-850 font-mono text-[10px] text-gray-300">
                  <p className="text-emerald-400">Options -Indexes</p>
                </div>
              </div>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
