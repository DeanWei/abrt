/*
    MiddleWare.h - header file for MiddleWare library. It wraps plugins and
                   take case of them.

    Copyright (C) 2009  Zdenek Prikryl (zprikryl@redhat.com)
    Copyright (C) 2009  RedHat inc.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    */


#ifndef MIDDLEWARE_H_
#define MIDDLEWARE_H_

#include "PluginManager.h"
#include <set>
#include <string>


class CMiddleWare
{
    public:

        typedef struct SCrashInfo
        {
            std::string m_sUUID;
            std::string m_sUID;
            std::string m_sCount;
            std::string m_sExecutable;
            std::string m_sPackage;
            std::string m_sTime;
        } crash_info_t;

        typedef struct SCrashReport
        {
            std::string m_sUUID;
            std::string m_sUID;
            std::string m_sPlugin2ReportersName;
            CReporter::report_t m_Report;
        } crash_report_t;

        typedef std::vector<crash_info_t> vector_crash_infos_t;

    private:
        typedef set_settings_t set_blacklist_t;
        typedef set_settings_t set_enabled_plugins_t;
        typedef set_settings_t set_reporters_t;
        typedef std::map<std::string, set_reporters_t> map_plugin2reporters_t;

        CPluginManager* m_pPluginManager;
        set_blacklist_t m_setBlackList;
        set_enabled_plugins_t m_setEnabledPlugins;
        std::string m_sDatabase;
        map_plugin2reporters_t m_mapPlugin2Reporters;


        std::string GetLocalUUIDLanguage(const std::string& pLanguage,
                                         const std::string& pDebugDumpDir);
        void CreateReportLanguage(const std::string& pLanguage,
                                     const std::string& pDebugDumpDir);
        std::string GetLocalUUIDApplication(const std::string& pApplication,
                                            const std::string& pDebugDumpDir);
        void CreateReportApplication(const std::string& pApplication,
                                     const std::string& pDebugDumpDir);

        void LoadSettings(const std::string& pPath);

        void DebugDump2Report(const std::string& pDebugDumpDir,
                              CReporter::report_t& pReport);
        void CreateReport(const std::string& pDebugDumpDir,
                          crash_report_t& pReport);

    public:

        CMiddleWare(const std::string& pPlugisConfDir,
                    const std::string& pPlugisLibDir,
                    const std::string& pMiddleWareConfFile);

        ~CMiddleWare();

        void RegisterPlugin(const std::string& pName);
        void UnRegisterPlugin(const std::string& pName);

        void CreateReport(const std::string& pUUID,
                          const std::string& pUID,
                          crash_report_t& pReport);
        void Report(const crash_report_t& pReport);

        int SaveDebugDump(const std::string& pDebugDumpPath, crash_info_t& pCrashInfo);
        vector_crash_infos_t GetCrashInfos(const std::string& pUID);
};

#endif /*MIDDLEWARE_H_*/
