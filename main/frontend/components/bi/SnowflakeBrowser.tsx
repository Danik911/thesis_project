import { useMemo, useState } from 'react';

import { getApiBaseUrl } from '@/lib/authenticatedFetch';
import type {
  BIUploadResponse,
  SnowflakeConnectRequest,
  SnowflakeLoadStageFileRequest,
  SnowflakeLoadTableRequest,
  SnowflakeStageFile,
  SnowflakeStageFilesResponse,
  SnowflakeTable,
  SnowflakeTablesResponse,
} from '@/types/bi';

interface SnowflakeBrowserProps {
  onSessionLoaded: (payload: BIUploadResponse) => void;
  onError: (message: string) => void;
}

type BrowseTab = 'tables' | 'stages';

export default function SnowflakeBrowser({ onSessionLoaded, onError }: SnowflakeBrowserProps) {
  const [sfAccount, setSfAccount] = useState('');
  const [sfUser, setSfUser] = useState('');
  const [sfPassword, setSfPassword] = useState('');
  const [sfWarehouse, setSfWarehouse] = useState('');
  const [sfDatabase, setSfDatabase] = useState('');
  const [sfSchema, setSfSchema] = useState('');

  const [connecting, setConnecting] = useState(false);
  const [loadingTable, setLoadingTable] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [connected, setConnected] = useState(false);

  const [browseTab, setBrowseTab] = useState<BrowseTab>('tables');
  const [tables, setTables] = useState<SnowflakeTable[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  const [stageName, setStageName] = useState('');
  const [stageFiles, setStageFiles] = useState<SnowflakeStageFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const canConnect = useMemo(
    () =>
      sfAccount.trim() &&
      sfUser.trim() &&
      sfPassword.trim() &&
      sfWarehouse.trim() &&
      sfDatabase.trim() &&
      sfSchema.trim(),
    [sfAccount, sfUser, sfPassword, sfWarehouse, sfDatabase, sfSchema]
  );

  const connectionPayload: SnowflakeConnectRequest = useMemo(
    () => ({
      account: sfAccount.trim(),
      user: sfUser.trim(),
      password: sfPassword,
      warehouse: sfWarehouse.trim(),
      database: sfDatabase.trim(),
      schema_name: sfSchema.trim(),
    }),
    [sfAccount, sfUser, sfPassword, sfWarehouse, sfDatabase, sfSchema]
  );

  const handleApiError = async (response: Response, fallback: string) => {
    const body = await response.json().catch(() => ({}));
    const message = typeof body?.detail === 'string' ? body.detail : fallback;
    onError(message);
  };

  const connect = async () => {
    if (!canConnect) {
      onError('All Snowflake connection fields are required');
      return;
    }

    setConnecting(true);
    onError('');

    try {
      const response = await fetch(`${getApiBaseUrl()}/bi/snowflake/tables`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(connectionPayload),
      });

      if (!response.ok) {
        await handleApiError(response, `Snowflake connect failed (${response.status})`);
        return;
      }

      const payload: SnowflakeTablesResponse = await response.json();
      setTables(payload.tables);
      setSelectedTable(payload.tables.length > 0 ? payload.tables[0].name : null);
      setConnected(true);
      setBrowseTab('tables');
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Snowflake connect failed');
    } finally {
      setConnecting(false);
    }
  };

  const loadSelectedTable = async () => {
    if (!selectedTable) {
      onError('Select a table to load');
      return;
    }

    const payload: SnowflakeLoadTableRequest = {
      ...connectionPayload,
      table_name: selectedTable,
    };

    setLoadingTable(true);
    onError('');

    try {
      const response = await fetch(`${getApiBaseUrl()}/bi/snowflake/load/table`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        await handleApiError(response, `Snowflake table load failed (${response.status})`);
        return;
      }

      const uploadPayload: BIUploadResponse = await response.json();
      onSessionLoaded(uploadPayload);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Snowflake table load failed');
    } finally {
      setLoadingTable(false);
    }
  };

  const listStageFiles = async () => {
    if (!stageName.trim()) {
      onError('Stage name is required');
      return;
    }

    setLoadingFiles(true);
    onError('');

    try {
      const response = await fetch(
        `${getApiBaseUrl()}/bi/snowflake/stages/${encodeURIComponent(stageName.trim())}/files`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(connectionPayload),
        }
      );

      if (!response.ok) {
        await handleApiError(response, `Snowflake stage listing failed (${response.status})`);
        return;
      }

      const payload: SnowflakeStageFilesResponse = await response.json();
      setStageFiles(payload.files);
      setSelectedFile(payload.files.length > 0 ? payload.files[0].name : null);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Snowflake stage listing failed');
    } finally {
      setLoadingFiles(false);
    }
  };

  const loadSelectedFile = async () => {
    if (!stageName.trim()) {
      onError('Stage name is required');
      return;
    }

    if (!selectedFile) {
      onError('Select a stage file to load');
      return;
    }

    const payload: SnowflakeLoadStageFileRequest = {
      ...connectionPayload,
      stage_name: stageName.trim(),
      file_path: selectedFile,
    };

    setLoadingTable(true);
    onError('');

    try {
      const response = await fetch(`${getApiBaseUrl()}/bi/snowflake/load/stage-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        await handleApiError(response, `Snowflake stage file load failed (${response.status})`);
        return;
      }

      const uploadPayload: BIUploadResponse = await response.json();
      onSessionLoaded(uploadPayload);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Snowflake stage file load failed');
    } finally {
      setLoadingTable(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-700/50 bg-slate-900/50 p-6 space-y-4">
      <p className="text-sm text-slate-300">Connect to Snowflake and load a table or stage file into BI.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <input
          value={sfAccount}
          onChange={(event) => setSfAccount(event.target.value)}
          placeholder="Account"
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        />
        <input
          value={sfUser}
          onChange={(event) => setSfUser(event.target.value)}
          placeholder="User"
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        />
        <input
          value={sfPassword}
          onChange={(event) => setSfPassword(event.target.value)}
          placeholder="Password"
          type="password"
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        />
        <input
          value={sfWarehouse}
          onChange={(event) => setSfWarehouse(event.target.value)}
          placeholder="Warehouse"
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        />
        <input
          value={sfDatabase}
          onChange={(event) => setSfDatabase(event.target.value)}
          placeholder="Database"
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        />
        <input
          value={sfSchema}
          onChange={(event) => setSfSchema(event.target.value)}
          placeholder="Schema"
          className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        />
      </div>

      <button
        type="button"
        onClick={connect}
        disabled={!canConnect || connecting}
        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
          !canConnect || connecting
            ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
            : 'bg-cyan-600 hover:bg-cyan-500 text-white'
        }`}
      >
        {connecting ? 'Connecting...' : 'Connect'}
      </button>

      {connected && (
        <div className="space-y-4 border-t border-slate-700/60 pt-4">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setBrowseTab('tables')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                browseTab === 'tables'
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-800 text-slate-300 border border-slate-700'
              }`}
            >
              Tables
            </button>
            <button
              type="button"
              onClick={() => setBrowseTab('stages')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                browseTab === 'stages'
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-800 text-slate-300 border border-slate-700'
              }`}
            >
              Stage Files
            </button>
          </div>

          {browseTab === 'tables' ? (
            <>
              <div className="rounded-lg border border-slate-700 bg-slate-800/40 max-h-72 overflow-auto">
                {tables.length === 0 ? (
                  <p className="px-3 py-2 text-sm text-slate-400">No tables found.</p>
                ) : (
                  <ul>
                    {tables.map((table) => {
                      const selected = selectedTable === table.name;
                      return (
                        <li key={table.name}>
                          <button
                            type="button"
                            onClick={() => setSelectedTable(table.name)}
                            className={`w-full text-left px-3 py-2 text-sm border-b border-slate-700/50 transition-colors ${
                              selected
                                ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-200'
                                : 'text-slate-200 hover:bg-slate-700/40'
                            }`}
                          >
                            <span className="font-medium">{table.name}</span>
                            <span className="ml-2 text-xs text-slate-400">
                              ({table.kind}, {table.row_count ?? 'n/a'} rows)
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              <button
                type="button"
                onClick={loadSelectedTable}
                disabled={!selectedTable || loadingTable}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  !selectedTable || loadingTable
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                }`}
              >
                {loadingTable ? 'Loading...' : 'Load Selected Table'}
              </button>
            </>
          ) : (
            <>
              <div className="flex gap-2">
                <input
                  value={stageName}
                  onChange={(event) => setStageName(event.target.value)}
                  placeholder="Stage name (e.g., DB.SCHEMA.MY_STAGE)"
                  className="flex-1 bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
                />
                <button
                  type="button"
                  onClick={listStageFiles}
                  disabled={!stageName.trim() || loadingFiles}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    !stageName.trim() || loadingFiles
                      ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                      : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                  }`}
                >
                  {loadingFiles ? 'Listing...' : 'List Files'}
                </button>
              </div>

              <div className="rounded-lg border border-slate-700 bg-slate-800/40 max-h-72 overflow-auto">
                {stageFiles.length === 0 ? (
                  <p className="px-3 py-2 text-sm text-slate-400">No files listed.</p>
                ) : (
                  <ul>
                    {stageFiles.map((file) => {
                      const selected = selectedFile === file.name;
                      return (
                        <li key={file.name}>
                          <button
                            type="button"
                            onClick={() => setSelectedFile(file.name)}
                            className={`w-full text-left px-3 py-2 text-sm border-b border-slate-700/50 transition-colors ${
                              selected
                                ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-200'
                                : 'text-slate-200 hover:bg-slate-700/40'
                            }`}
                          >
                            <span className="font-medium">{file.name}</span>
                            <span className="ml-2 text-xs text-slate-400">({file.size} bytes)</span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              <button
                type="button"
                onClick={loadSelectedFile}
                disabled={!selectedFile || loadingTable}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  !selectedFile || loadingTable
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                }`}
              >
                {loadingTable ? 'Loading...' : 'Load Selected File'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
