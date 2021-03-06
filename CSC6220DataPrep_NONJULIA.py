'''
Data for CSC6220 
Jan 05, 2019 
Akond Rahman 
'''
import pandas as pd 
import numpy as np 

import _pickle as pickle
import time
import datetime
import os 
import csv 
import sys
from git import Repo
import  subprocess
import time 
import  datetime 
from collections import Counter

def giveTimeStamp():
  tsObj = time.time()
  strToret = datetime.datetime.fromtimestamp(tsObj).strftime('%Y-%m-%d %H:%M:%S')
  return strToret

def getEligibleProjects(fileNameParam):
  repo_list = []
  with open(fileNameParam, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
      repo_list.append(row[0])
  return repo_list

def getModFilesInDiff(diff_str):
    mod_files  = []
    splitted_lines = diff_str.split('\n')
    for x_ in splitted_lines:
      if '/' in x_  and '.' in x_: 
        if '---' in x_:
          # print(splitted_lines) 
          del_ =  x_.split(' ')[-1].replace('a', '')
          mod_files.append(del_) 
        elif '+++' in x_:
          # print(splitted_lines) 
          add_ =  x_.split(' ')[-1].replace('b', '')
          mod_files.append(add_)
    mod_files = np.unique(mod_files) 
    mod_files = [x_ for x_ in mod_files if ('doc' not in x_) and ('test' not in x_) ]
    # print(mod_files)
    # print(';'*25)
    return mod_files

def getDiff(repo_, hash_):
    mod_files_list = []
   
    cdCommand   = "cd " + repo_ + " ; "
   
    diffCommand = "git diff " + hash_ + "~" + " " + hash_
    command2Run = cdCommand + diffCommand
    try:
      diff_output = subprocess.check_output(["bash", "-c", command2Run])
      diff_output =  diff_output.decode('latin-1') ### exception for utf-8 
      # print(diff_output) 
      mod_files_list =  getModFilesInDiff(diff_output)
    except subprocess.CalledProcessError as e_:
      diff_output = "NOT_FOUND" 
    return diff_output, mod_files_list

def filterFiles(ls_):
  mod_list = [] 
  for elem in ls_:
    z_  = elem.split('.')[-1].lower() 
    # print(z_) 
    if ( ('md' not in z_)   and ('rst' not in z_) and  \
                                  ('html' not in z_) and ('txt' not in z_) and  \
                                  ('json' not in z_) and ('test' not in z_) and  \
                                  ('html' not in z_) and ('image' not in z_) and  \
                                  ('git' not in z_) and  ('dat' not in z_)  and ('travis' not in z_) and  ('inl' not in z_) and \
                                  ('mod' not in z_) and  ('cfg' not in z_)  and ('json' not in z_) and  ('xml' not in z_)   ): 
                                  mod_list.append( elem  ) 
  return mod_list 


def dumpContentIntoFile(strP, fileP):
    fileToWrite = open( fileP, 'w')
    fileToWrite.write(strP)
    fileToWrite.close()
    return str(os.stat(fileP).st_size)


def getFileContent(file_name):
  full_data = ''
  f = open(file_name, 'r', encoding='latin-1')
  full_data = f.read()
  return full_data 


def getSecuFileMapping(full_df, repo_type): 
  secu_file = []
  all_files = np.unique(full_df['FILE_MAP'].tolist()) 
  all_repos = np.unique(full_df['REPO_PATH'].tolist() )
  file_secu = 'NEUTRAL'
  for file_ in all_files: 
    file_df = full_df[full_df['FILE_MAP']==file_] 
    file_flags = file_df['SECU_FLAG'].tolist() 
    file_size  = file_df['FILE_SIZE'].tolist()[0]
    file_ext   = file_.split('.')[-1].upper() 
    unique_flags = np.unique(file_flags)
    if (len(unique_flags) ==1 ) and (unique_flags[0]=='NEUTRAL'):
      file_secu = 'NEUTRAL'     
    else:
      file_secu = 'INSECURE' 
    if ((file_ext=='C') or (file_ext=='CC') or (file_ext=='CPP')  or (file_ext=='GO') or (file_ext=='H') or (file_ext=='HH') or (file_ext=='HPP') or (file_ext=='JAVA') or (file_ext=='JL') or (file_ext=='JS') or (file_ext=='LUA') or (file_ext=='PL')  or (file_ext=='PY') or (file_ext=='R') or (file_ext=='RB')  ):    
      tu = (file_ , file_size , file_ext, file_secu) 
      secu_file.append( tu )
  secu_df = pd.DataFrame(secu_file)
  secu_df.to_csv(repo_type + '_SECU_FILE_MAP.csv', header=[ 'FILE_MAP', 'FILE_SIZE' , 'FILE_EXT', 'SECU_FLAG' ], index=False, encoding='utf-8')   
  print('TOTAL REPOS:', len(all_repos)) 

    

def getSummary(df_param): 
  repo_names = np.unique(df_param['REPO'].tolist()) 
  for repo_ in repo_names:
    print('*'*100 )
    print('REPO:{}, HASHES:{}'.format(repo_, len(np.unique( df_param[ df_param['REPO']==repo_]['HASH'].tolist()   )) ))
    print('*'*100 )

 
def buildContent(df_, HOST_DIR, repo_type, out_dir):
    content = [] 
    repo_df  = df_[df_['REPO_TYPE']==repo_type]
    getSummary(repo_df) 
    all_repo_cnt = len( np.unique(repo_df['REPO'].tolist()) )  
    print('TOTAL REPOS ARE {} FOR {}'.format(  all_repo_cnt, repo_type) ) 
    all_hash = np.unique( repo_df['HASH'].tolist() ) 
    already_seen = []
    for hash_ in all_hash: 
        hash_df = df_[df_['HASH']==hash_]
        repo_name = hash_df['REPO'].tolist()[0]
        secu_flag = hash_df['SECU_FLAG'].tolist()[0] 
        repo_path = HOST_DIR + repo_name + '/'
        diff_txt, file_list  = getDiff(repo_path, hash_) 
        repo_type = hash_df['REPO_TYPE'].tolist()[0] 
        tot_loc   = hash_df['TOT_LOC'].tolist()[0] 
        if tot_loc > 0:
          filtered_files = filterFiles(file_list) 
          # print(repo_path, filtered_files) 
          # print('<>'*25)
          for fil_ in filtered_files: 
            file_path     = HOST_DIR + repo_name + fil_ 
            try:
              if(os.path.exists(file_path)) and (os.path.isdir(file_path) == False):  
                num_lines     = sum(1 for line in open( file_path , 'r',  encoding='latin-1' ))
                map_name      = file_path.replace('/', '_')
                tuple_        = (repo_name, repo_path, repo_type, hash_, file_path, num_lines , map_name, secu_flag)  
                # print(tuple_) 
                content.append( tuple_ )
                if map_name not in already_seen:
                  out_file_name = out_dir + map_name 
                  out_file_content = getFileContent(file_path) 
                  dumpContentIntoFile(out_file_content, out_file_name)
                  already_seen.append(map_name) 
                  print('Dumped', file_path) 
            except ValueError as e_:
              print(e_) 
              print(hash_) 
    mapping_df = pd.DataFrame(content) 
    mapping_df.to_csv(repo_type + '.csv', header=['REPO_NAME', 'REPO_PATH', 'REPO_TYPE', 'HASH', 'FILE_PATH', 'FILE_SIZE',  'FILE_MAP', 'SECU_FLAG' ], index=False, encoding='utf-8')   
    df = pd.read_csv(repo_type + '.csv') 
    getSecuFileMapping( df , repo_type )


def filterText(msg_commit):
    msg_commit = msg_commit.replace('\n', ' ')
    msg_commit = msg_commit.replace(',',  ';')    
    msg_commit = msg_commit.replace('\t', ' ')
    msg_commit = msg_commit.replace('&',  ';')  
    msg_commit = msg_commit.replace('#',  '')
    msg_commit = msg_commit.replace('=',  '')      
    msg_commit = msg_commit.replace('-',  '')  
    msg_commit = msg_commit.replace(':',  '')
    msg_commit = msg_commit.replace('.',  '')      
    msg_commit = msg_commit.replace('\r',  '')      

    return msg_commit


def getDiffText(repo_, hash_):   
    cdCommand   = "cd " + repo_ + " ; "
   
    diffCommand = "git log --format=%B -n 1 " + hash_ 
    command2Run = cdCommand + diffCommand
    try:
      diff_output = subprocess.check_output(["bash", "-c", command2Run])
      diff_output =  diff_output.decode('latin-1') ### exception for utf-8 
    except subprocess.CalledProcessError as e_:
      diff_output = "NOT_FOUND" 
    diff_output = filterText(diff_output) 

    # print(diff_output)
    return diff_output


def detectBuggyCommit(msg_):
    prem_bug_kw_list      = ['error', 'bug', 'fix', 'issue', 'mistake', 'incorrect', 'fault', 'defect', 'flaw', 'solve' ]
    flag2ret  = 0 
    msg_ = msg_.lower()
    if(any(x_ in msg_ for x_ in prem_bug_kw_list)) and ( 'default' not in msg_) and ('merge' not in msg_) :    
        flag2ret = 1 
    return flag2ret

def getCommitMessageCSV(type2analyze): 
  all_content = []
  df_    = pd.read_csv( type2analyze + '.csv') 
  hashes = np.unique(  df_['HASH'].tolist() ) 
  for hash_ in hashes:
    hash_df      = df_[df_['HASH']==hash_]
    repo_path    = hash_df['REPO_PATH'].tolist()[0]  
    hash_message = getDiffText(repo_path, hash_) 
    hash_message = filterText(hash_message) 
    bug_flag     = detectBuggyCommit(hash_message) 
    all_content.append( (repo_path, hash_ , hash_message, bug_flag) ) 
  all_df_ = pd.DataFrame( all_content )
  all_df_.to_csv(type2analyze +  '_BUG_FLAG.csv', header=['REPO', 'HASH', 'MESSAGE', 'BUG_FLAG' ], index=False, encoding='utf-8')  
  print('Unique repos:', len( np.unique(df_['REPO_PATH'].tolist() ) ) )

def getBugFileMapping(filtered_file, full_file, repo_type): 
  buggy_file = []
  full_df   = pd.read_csv(full_file) 
  all_files = np.unique(full_df['FILE_MAP'].tolist()) 
  filtered_df = pd.read_csv(filtered_file) 
  file_label  = 'NEUTRAL'
  for file_ in all_files: 
    file_df = full_df[full_df['FILE_MAP']==file_] 
    file_size  = file_df['FILE_SIZE'].tolist()[0]
    file_ext   = file_.split('.')[-1].upper() 
    file_hash  = file_df['HASH'].tolist() 

    filtered_file_df = filtered_df[filtered_df['HASH'].isin(file_hash)] 
    # print(filtered_file_df) 
    unique_flags     = np.unique( filtered_file_df['BUG_FLAG'].tolist() )

    if (len(unique_flags) ==1 ) and (unique_flags[0]==0):
      file_label = 'NEUTRAL'     
    else:
      file_label = 'BUGGY' 
    if ((file_ext=='C') or (file_ext=='CC') or (file_ext=='CPP')  or (file_ext=='GO') or (file_ext=='H') or (file_ext=='HH') or (file_ext=='HPP') or (file_ext=='JAVA') or (file_ext=='JL') or (file_ext=='JS') or (file_ext=='LUA') or (file_ext=='PL')  or (file_ext=='PY') or (file_ext=='R') or (file_ext=='RB')  ):    
      tu = (file_ , file_size , file_ext, file_label) 
      buggy_file.append( tu )
  buggy_df = pd.DataFrame(buggy_file)
  buggy_df.to_csv(repo_type + '_BUGGY_FILE_MAP.csv', header=[ 'FILE_MAP', 'FILE_SIZE' , 'FILE_EXT', 'BUG_FLAG' ], index=False, encoding='utf-8')   


if __name__=='__main__': 

    t1 = time.time()
    print('Started at:', giveTimeStamp() )
    print('*'*100 )

    CURATED_FILE = '/Users/arahman/Documents/OneDriveWingUp/OneDrive-TennesseeTechUniversity/Teaching/Spring2020/CSC6220-TNTECH/CURATED_SECURITY_FULL.csv' 
    HOST_DIR='/Users/arahman/TEACHING_REPOS/NON_JULIA_SCIENTIFIC_SOFTWARE/'
    OUTPUT_DIR = '/Users/arahman/Documents/OneDriveWingUp/OneDrive-TennesseeTechUniversity/Teaching/Spring2020/CSC6220_DATASET/'
    CURATED_DF   = pd.read_csv(CURATED_FILE) 

    # TYPE2ANALYZE = 'ComputationalBiology'

    # TYPE2ANALYZE = 'Astronomy'

    TYPE2ANALYZE = 'ComputationalChemistry'

    ### First we got everything related to security 
    # buildContent(CURATED_DF, HOST_DIR, TYPE2ANALYZE, OUTPUT_DIR)  
    ### Then we mapped security labels to files 
    # getSecuFileMapping( pd.read_csv( TYPE2ANALYZE + '.csv') , TYPE2ANALYZE )
    ### Then we mapped bug labels to files 
    # getCommitMessageCSV(TYPE2ANALYZE) 

    ### Then we mapped bug labels to files 
    getBugFileMapping('Filtered_' + TYPE2ANALYZE + '_BUG_FLAG.csv' , TYPE2ANALYZE + '.csv', TYPE2ANALYZE )


    print('*'*100 )
    print('Ended at:', giveTimeStamp() )
    print('*'*100 )
    t2 = time.time()
    time_diff = round( (t2 - t1 ) / 60, 5) 
    print('Duration: {} minutes'.format(time_diff) )
    print( '*'*100  )

    '''
    not used 
    getSecuFileMapping( pd.read_csv( TYPE2ANALYZE + '.csv') , TYPE2ANALYZE )
    '''
