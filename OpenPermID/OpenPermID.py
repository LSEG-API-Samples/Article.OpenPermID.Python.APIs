import requests
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import pandas as pd
import os

 
class OpenPermID(object):
    __access_token__=""
    __lookupurl__="https://permid.org/"
    __searchurl__="https://api-eit.refinitiv.com/permid/search"
    __matchurl__="https://api-eit.refinitiv.com/permid/match"
    __matchFileurl__="https://api-eit.refinitiv.com/permid/match/file"
    __calaisurl__ ="https://api-eit.refinitiv.com/permid/calais"
    __timeout__ = 30
    __response__ = None
    __quota__ = []
    __max_log_size__ = 10000000
    __backupCount__ = 10
    __log_file_name__ = "openpermid"
    __log_path__ = None
    __log_format__ = "%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s \n"

    def __init__(self):
        self.__access_token__=""
        self.log_path = None
        self.log_level = logging.NOTSET       
        self.logger = logging.getLogger('openpermid')

    def set_log_format(self, format):
        self.__log_format__ = format

    def set_log_max_size(self, size):
        self.__max_log_size__ = size

    def set_log_path(self, log_path):       
        if os.access(log_path, os.W_OK):
            self.__log_path__ = log_path
            return True
        else:
            return False

    def set_log_file_name(self, name):
        self.__log_file_name__ = name

    def set_log_backup_count(self, count):
        self.__backupCount__ = count

    def set_lookup_url(self, url):
        self.__lookupurl__ = url

    def set_search_url(self, url):
        self.__searchurl__ = url

    def set_match_url(self, url):
        self.__matchurl__ = url

    def set_matchFile_url(self, url):
        self.__matchFileurl__ = url

    def set_calais_url(self, url):
        self.__calaisurl__ = url

    def set_timeout(self, timeout):
        self.__timeout__ = timeout


    def get_response(self):
        return self.__response__

    def get_usage(self):
        if(len(self.__quota__)==0):
            return pd.DataFrame([{'Time':'None', 'Quota Daily':'None', 'Quota Used':'None'}])

        return pd.DataFrame(self.__quota__)

    def set_log_level(self, log_level):
        if log_level > logging.NOTSET:
            __formatter = logging.Formatter(self.__log_format__)
            __filename = '{0}_{1}.{2}.log'.format(self.__log_file_name__, os.getpid(), datetime.now().strftime('%Y%m%d.%H-%M-%S'))
            
            if self.__log_path__ is not None:
                if not os.path.isdir(self.__log_path__):
                    os.makedirs(self.__log_path__)
                __filename = os.path.join(self.__log_path__, __filename)

            __handler = logging.handlers.RotatingFileHandler(__filename, mode='a', maxBytes=self.__max_log_size__,
                                                        backupCount=self.__backupCount__, encoding='utf-8')
            
            __handler.setFormatter(__formatter)
            self.logger.addHandler(__handler)

        self.logger.setLevel(log_level)
        self.log_level = log_level

    def get_log_level(self):
        """
        Returns the log level
        """
        return self.logger.level


    def set_access_token(self, token):
        self.__access_token__ = token

    def set_lookup_url(self, url):
        self.__lookupurl__ = url

    def __record_usage__(self, response):
        quota_daily = None
        quota_used = None
        timestamp = None
        
        if('x-permid-quota-daily' in response.headers):
            quota_daily = response.headers['x-permid-quota-daily']

        if('x-permid-quota-used' in response.headers):
            quota_used = response.headers['x-permid-quota-used']

        if(quota_daily != None or quota_used != None):
            
            if('Date' in response.headers):
                timestamp = response.headers['Date']
            else:                
                timestamp = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

            self.__quota__.append({'Time':timestamp, 'Quota Daily':quota_daily, 'Quota Used':quota_used})
            
                               

        


    def __post__(self, url, headers, body=None, filename=None):
        self.logger.debug('Post: %s, %s, %s, %s', url, headers, body, filename)
        self.__response__ = None
        try:
            if (filename == None):
                response = requests.post(
                    url,
                    headers=headers,
                    data = body,
                    timeout=self.__timeout__)
            else:
                files = {'file': open(filename)}
                response = requests.post(
                    url,
                    headers=headers,
                    files = files,
                    timeout=self.__timeout__)
            
            
        except requests.exceptions.ReadTimeout as e:
            self.logger.debug('ReadTimeout: %s', e)
            return None, e 
        except requests.exceptions.RequestException as e:
            self.logger.debug('RequestException: %s', e)
            return None, e 
        self.__response__ = response
        self.logger.debug('Response: %s, %s, %s', response, response.headers, response.text)
        if(response.status_code == requests.codes.ok and response.headers["Content-Type"]=='text/html'):
            self.logger.error("%s, %s, %s", response, response.headers, response.text[0:200])
            return None, "Not Found"

        if(response.status_code != requests.codes.ok):
            self.logger.error("%s, %s, %s", response, response.headers, response.text[0:200])
            return None, response.reason+': '+response.text

        
        self.__record_usage__(response)
        #if('x-permid-quota-daily' in response.headers):
        #    self.__quotaDaily__ = response.headers['x-permid-quota-daily']

        #if('x-permid-quota-used' in response.headers):
        #    self.__quotaUsed__ = response.headers['x-permid-quota-used']
        
        return response.text, None
        
    def __request__(self, url, headers, params):
        self.logger.debug('Request: %s, %s, %s', url, headers, params)
        self.__response__ = None
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.__timeout__
                )
            
        except requests.exceptions.ReadTimeout as e:
           self.logger.debug('ReadTimeout: %s', e)
           return None, e
        except requests.exceptions.RequestException as e:
            self.logger.debug('RequestException: %s', e)
            return None, e 

        self.__response__ = response
        self.logger.debug('Response: %s, %s, %s', response, response.headers, response.text)
        if(response.status_code == requests.codes.ok and "Content-Type" not in response.headers):
            self.logger.error("%s, %s, %s", response, response.headers, response.text[0:200])
            return None, "Not Found"

        if(response.status_code != requests.codes.ok):
            self.logger.error("%s, %s, %s", response, response.headers, response.text[0:200])
            return None, response.reason+': '+response.text   
        
        self.__record_usage__(response)
        #if('x-permid-quota-daily' in response.headers):
        #    self.__quotaDaily__ = response.headers['x-permid-quota-daily']

        #if('x-permid-quota-used' in response.headers):
        #    self.__quotaUsed__ = response.headers['x-permid-quota-used']
        
        return response.text, None

    def matchFile(self,
                  filename='',
                  dataType='Organization',
                  numberOfMatchesPerRecord=1,
                  raw_output=False
                  ):
        self.logger.info("match: %s, %s, %s", numberOfMatchesPerRecord, dataType, filename)
        if( os.path.exists(filename) == False):
            self.logger.error('%s doesn\'t exist.', filename)
            return None,"File doesn't exist."
        _headers={}
        if(dataType not in ['Organization','Person','Instrument','Quote']):
            self.logger.error('Invalid dataType for match: %s', dataType)
            return None,"The valid dataTypes are 'Organization','Person','Instrument',and 'Quote'."

        if 1 < numberOfMatchesPerRecord > 5:
             self.logger.error('Invalid numberOfMatchesPerRecord for match: %s', numberOfMatchesPerRecord)
             return None,"The valid numberOfMatchesPerRecord are 1 - 5."

        if(self.__access_token__!=""):
            _headers["x-ag-access-token"] = self.__access_token__
        
       
        _headers["Accept"]='application/json'
        _headers["x-openmatch-numberOfMatchesPerRecord"] = str(numberOfMatchesPerRecord)
        _headers["x-openmatch-dataType"] = dataType

        resp, err = self.__post__(
            url=self.__matchFileurl__,
            headers=_headers,
            filename=filename)
        

        if(raw_output==True or resp==None):
            return resp, err
        else:
            jsonObj=json.loads(resp)
            return  pd.DataFrame.from_dict(jsonObj['outputContentResponse']), err

    def match(self,
              data='',
              dataType='Organization',
              numberOfMatchesPerRecord=1,
              raw_output=False
              ):
        self.logger.info("match: %s, %s, %s", numberOfMatchesPerRecord, dataType, data)
        _headers={}


        if(dataType not in ['Organization','Person','Instrument','Quote']):
            self.logger.error('Invalid dataType for match: %s', dataType)
            return None,"The valid dataTypes are 'Organization','Person','Instrument',and 'Quote'."

        if 1 < numberOfMatchesPerRecord > 5:
             self.logger.error('Invalid numberOfMatchesPerRecord for match: %s', numberOfMatchesPerRecord)
             return None,"The valid numberOfMatchesPerRecord are 1 - 5."

        if(self.__access_token__!=""):
            _headers["x-ag-access-token"] = self.__access_token__  

        text = ""
        if isinstance(data, pd.DataFrame):
            if data.empty:
                self.logger.error('dataframe is empty.')
                return None, "dataframe is empty"
            text = data.to_csv(index=False)            
        elif isinstance(data, str):
            if not data:
                self.logger.error('data is required: %s', data)
                return None, "data is required"
            text = data
        else:
             self.logger.error('data must be dataframe or string.')
             return None,"data must be dataframe or string."
        
        _headers["Content-Type"] = 'text/plain'
        _headers["Accept"]='application/json'
        _headers["x-openmatch-numberOfMatchesPerRecord"] = str(numberOfMatchesPerRecord)
        _headers["x-openmatch-dataType"] = dataType

     


        resp, err = self.__post__(
            url=self.__matchurl__,
            headers=_headers,
            body=text)
        

        if(raw_output==True or resp==None):
            return resp, err
        else:
            jsonObj=json.loads(resp)
            return  pd.DataFrame.from_dict(jsonObj['outputContentResponse']), err

    def search(self,
               q,
               entityType='all', #all, organization, instrument, quote
               format='dataframe', #dataframe, json, xml,
               start=1,
               num=5,
               order='rel' #rel, az, za
               ):
        self.logger.info("search: %s, %s, %s, %s, %s, %s", q, entityType, format,start,num,order)
        _params={}
        if(entityType not in ['all','organization','instrument','quote']):
            self.logger.error('Invalid entitytype for search: %s', entitytype)
            return None,"The valid entity types are 'all', 'organizaion', 'instrument', and'quote'."
        if(format not in ['dataframe','json','xml']):
            self.logger.error('Invalid format for search %s', format)
            return None,"The valid formats are 'dataframe', 'json',and 'xml'."
        if(order not in ['rel','az','za']):
            self.logger.error('Invalid order for search %s', order)
            return None,"The valid orders are 'rel', 'az',and 'za'."

        if(format=="dataframe"):
            _params["format"] = 'json'
        else:
            _params["format"] = format

        if(self.__access_token__!=""):
            _params["access-token"] = self.__access_token__  

        _params["q"]=q
        if(entityType != 'all'):
            _params["entityType"]=entityType
        _params["num"]=num
        _params["order"]=order
        _params["start"]=start

        resp, error = self.__request__(
            self.__searchurl__,
            params=_params,
            headers={})

        if(resp==None):
            return None, error
      
        if(format!='dataframe'):
            return resp, None
     
        
        jsonObj=json.loads(resp)
       
       
        if(entityType=='all'):
            dfDict={}
            for (attribute, value) in jsonObj['result'].items():
                df = pd.DataFrame.from_dict(value['entities'])
                dfDict[attribute]=df
            return dfDict, None
        else:
            result = jsonObj['result']
            firstKey = next(iter(result))             
            return pd.DataFrame.from_dict(result[firstKey]['entities']), None
            

        

    def lookup(self, 
               id, 
               format="dataframe",
               orient="row"):
        self.logger.info("lookup: %s, %s, %s", id, format, orient)
        _params={}
        _header={'Accept':'application/ld+json'}
        if(format not in ['dataframe', 'json-ld','turtle']):
            self.logger.error('Invalid format for lookup: %s', format)
            return None,"The valid formats are 'dataframe', 'json-ld', and 'turtle'."        

        if(format == 'dataframe' and orient not in ['row', 'column']):
            self.logger.error('Invalid orient for lookup: %s', orient)
            return None,"The valid orients for dataframe are 'row', and 'column'."        
            
        if(format=="dataframe"):
            _params["format"] = "json-ld"
        else:
            _params["format"] = format

        if(self.__access_token__!=""):
            _params["access-token"] = self.__access_token__               
       
        if(format=="turtle"):
            _header["Accept"]="text/turtle"
         
     
        resp, error = self.__request__(
            self.__lookupurl__+id,
            params=_params,
            headers=_header)

        if(resp==None):
            return None, error

        if(format!='dataframe'):
            return resp, None

        #Format the dataframe and return the dataframe to the caller
        #1. Remove '@context' from the json-ld 
        jsonObj=json.loads(resp)
        del jsonObj['@context']
        #2. Format the dataframe according to the orient parameter
        if(orient=='row'):
            df = pd.DataFrame.from_dict([jsonObj])
        else:
            df = pd.DataFrame.from_dict(jsonObj, orient='index',columns=[id])

        return df, None

    def calais(self,
               text,
               language='English',
               contentType='raw',
               outputFormat='json'):
        self.logger.info("calais: %s, %s, %s, %s", text, language, contentType, outputFormat)
        _headers={}


        #if(language not in ['English','Chinese','French','German','Japanese','Spanish']):
        #    self.logger.error('Invalid language for calais: %s', language)
        #    return None,"The valid languages are 'English','Chinese','French','German','Japanese', and 'Spanish'."

        if(contentType not in ['raw','html','xml','pdf']):
        #if(contentType not in ['raw','html','xml']):
            self.logger.error('Invalid contentType for calais: %s', contentType)
            return None,"The valid contentTypes are 'raw','html','xml', and 'pdf'."
            #return None,"The valid contentTypes are 'raw','html',and 'xml'."

        if(outputFormat not in ['json','rdf','n3']):
            self.logger.error('Invalid outputFormat for calais: %s', outputFormat)
            return None,"The valid outputFormats are 'json','rdf', and 'n3'."

        if (contentType == 'pdf'):
            contentType = 'application/'+contentType
        else:
            contentType = 'text/'+contentType

       
        if(outputFormat == 'rdf'):
            outputFormat = 'xml/'+outputFormat
        elif(outputFormat == 'n3'):
            outputFormat = 'text/'+outputFormat
        else:
            outputFormat = 'application/json'

        if(self.__access_token__!=""):
            _headers["x-ag-access-token"] = self.__access_token__  

        _headers["x-calais-language"] = language
        _headers["outputFormat"] = outputFormat
        _headers["Content-Type"] = contentType
        resp, err = self.__post__(
            url=self.__calaisurl__,
            headers=_headers,
            body=text)

        if(resp==None):
            return None, err
        else:
            return resp, None
