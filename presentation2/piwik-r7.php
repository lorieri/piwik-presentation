<?php
/**
 * Ripped from:
 * Piwik - Open source web analytics
 *
 * @link http://piwik.org
 * @license http://www.gnu.org/licenses/gpl-3.0.html GPL v3 or later
 * @version $Id: piwik.php 4599 2011-04-29 17:08:49Z vipsoft $
 *
 * @package Piwik
 */
$GLOBALS['PIWIK_TRACKER_DEBUG'] = false;
$GLOBALS['PIWIK_TRACKER_DEBUG_FORCE_SCHEDULED_TASKS'] = false;
define('PIWIK_ENABLE_TRACKING', true);

define('PIWIK_DOCUMENT_ROOT', dirname(__FILE__)=='/'?'':dirname(__FILE__));
if(file_exists(PIWIK_DOCUMENT_ROOT . '/bootstrap.php'))
{
    require_once PIWIK_DOCUMENT_ROOT . '/bootstrap.php';
}

$GLOBALS['PIWIK_TRACKER_MODE'] = true;
error_reporting(E_ALL|E_NOTICE);
@ini_set('xdebug.show_exception_trace', 0);
@ini_set('magic_quotes_runtime', 0);

if(!defined('PIWIK_USER_PATH'))
{
    define('PIWIK_USER_PATH', PIWIK_DOCUMENT_ROOT);
}
if(!defined('PIWIK_INCLUDE_PATH'))
{
    define('PIWIK_INCLUDE_PATH', PIWIK_DOCUMENT_ROOT);
}
@ignore_user_abort(true);

require_once PIWIK_INCLUDE_PATH .'/libs/upgradephp/upgrade.php';
require_once PIWIK_INCLUDE_PATH .'/libs/Event/Dispatcher.php';
require_once PIWIK_INCLUDE_PATH .'/libs/Event/Notification.php';
require_once PIWIK_INCLUDE_PATH .'/core/PluginsManager.php';
require_once PIWIK_INCLUDE_PATH .'/core/Plugin.php';
require_once PIWIK_INCLUDE_PATH .'/core/Common.php';
require_once PIWIK_INCLUDE_PATH .'/core/IP.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker/Config.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker/Db.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker/IgnoreCookie.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker/Visit.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker/GoalManager.php';
require_once PIWIK_INCLUDE_PATH .'/core/Tracker/Action.php';
require_once PIWIK_INCLUDE_PATH .'/core/CacheFile.php';
require_once PIWIK_INCLUDE_PATH .'/core/Cookie.php';

class Piwik_Tracker_R7 extends Piwik_Tracker {

    protected function end()
    {
        switch($this->getState())
        {
            case self::STATE_LOGGING_DISABLE:
                printDebug("Logging disabled, display transparent logo");
                $this->outputTransparentGif();
            break;

            case self::STATE_EMPTY_REQUEST:
                printDebug("Empty request => Piwik page");
                echo "<a href='/'>Piwik</a> is a free open source <a href='http://piwik.org'>web analytics</a> alternative to Google analytics.";
            break;

            case self::STATE_NOSCRIPT_REQUEST:
            case self::STATE_NOTHING_TO_NOTICE:
            default:
                printDebug("Nothing to notice => default behaviour");
                $this->outputTransparentGif();
            break;
        }
        printDebug("End of the page.");

        if($GLOBALS['PIWIK_TRACKER_DEBUG'] === true)
        {
            if(isset(self::$db)) {
                self::$db->recordProfiling();
                Piwik::printSqlProfilingReportTracker(self::$db);
            }
        }

    }
}

session_cache_limiter('nocache');
@date_default_timezone_set('UTC');

if(!defined('PIWIK_ENABLE_TRACKING') || PIWIK_ENABLE_TRACKING)
{
    ob_start();
}
if($GLOBALS['PIWIK_TRACKER_DEBUG'] === true)
{
    require_once PIWIK_INCLUDE_PATH .'/core/Loader.php';
    require_once PIWIK_INCLUDE_PATH .'/core/ErrorHandler.php';
    require_once PIWIK_INCLUDE_PATH .'/core/ExceptionHandler.php';
    $timer = new Piwik_Timer();
    set_error_handler('Piwik_ErrorHandler');
    set_exception_handler('Piwik_ExceptionHandler');
    printDebug("Debug enabled - Input parameters: <br/>" . var_export($_GET, true));
    Piwik_Tracker_Db::enableProfiling();
    // Config might have been created by proxy-piwik.php
    try {
        $config = Zend_Registry::get('config');
    } catch (Exception $e) {
        Piwik::createConfigObject();
    }
    Piwik::createLogObject();
}

if(!defined('PIWIK_ENABLE_TRACKING') || PIWIK_ENABLE_TRACKING)
{
    if (($handle = fopen($_SERVER['argv'][2], "r")) !== FALSE) #getting CSV file as argument 
    {
        while (($data = fgetcsv($handle)) !== FALSE)
        {
            $num = count($data);
            if ($num == 9 )
            {
                $idsite = $data[0];
                $url = $data[1];
                $action_name = $data[2];
                $cip = $data[3];
                $_id = $data[4];
                $cdt = $data[5];
                $rand = $data[6];
                $token_auth = $data[7];
                $_SERVER["HTTP_USER_AGENT"]= $data[8]; #replacing User Agent
                $r7_tracker = "action_name=" . $action_name . "&idsite=" . $idsite . "&rand=" . $rand . "&rec=1&url=" . $url . "&cip=" . $cip . "&token_auth=" . $token_auth . "&_id=" . $_id . "&cdt=" . $cdt;
                parse_str($r7_tracker,$tmp);
                $_GET = array_merge($_GET, $tmp);
                $process = new Piwik_Tracker_R7();
                $process->main();
                if($GLOBALS['PIWIK_TRACKER_DEBUG'] === true)
                {
                    printDebug($_COOKIE);
                    printDebug($timer);
                }
            }
        }
        fclose($handle);
        unlink($_SERVER['argv'][2]); #removing CSV file
    }
    ob_end_flush();
    fclose($handle);
}

?>
