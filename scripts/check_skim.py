#!/usr/bin/env python
# The ./jobscript_check.py should return 'success' or 'fail' or 'to_submit' or 'submitted' for a job_log_string
# The input is given as sys.argv[1] = queue_system.compress_string(job_log_string) sys.argv[2] = queue_system.compress_string(job_argument_string)
import sys
import os
import argparse
import shlex
import queue_system
from ROOT import TChain
from skim_file import get_cuts

#def get_args(keys, job_argument_string):
#  parser = argparse.ArgumentParser()
#  for key in keys:
#    parser.add_argument('--'+key)
#  args, unknown_args = parser.parse_known_args(shlex.split(job_argument_string))
#  return vars(args)
#
## key_pairs = [(-key, --key)]
#def get_args_from_key_pairs(key_pairs, job_argument_string):
#  parser = argparse.ArgumentParser()
#  for dkey, ddkey in key_pairs:
#    parser.add_argument('-'+dkey, '--'+ddkey)
#  args, unknown_args = parser.parse_known_args(shlex.split(job_argument_string))
#  return vars(args)
#
#def argument_string_to_dict(job_argument_string):
#  command_arg_string = get_args(['command'], job_argument_string)['command']
#  command_args = get_args_from_key_pairs([['m', 'mass'], ['l', 'mass_lsp'], ['k', 'skim_name'], 
#                           ['i', 'input_paths'], ['o', 'output_dir']], command_arg_string)
#  return command_args

# job_argument_string = "/net/top/homes/oshiro/code/nano2pico/scripts/skim_file.py -k 2l -i /net/cms29/cms29r0/pico/NanoAODv5/ttz_cordellbankv2/2016/data/unskimmed/pico_Run2016B_0_SingleElectron_SingleMuon_Nano1June2019-v1_runs275290.root -o /net/cms29/cms29r0/pico/NanoAODv5/ttz_cordellbankv2/2016/data/skim_2l/"
#job_argument_string = '--command="/net/top/homes/oshiro/code/nano2pico/scripts/skim_file.py -m 127 -i "/net/cms29/cms29r0/pico/NanoAODv5/nano/2018/SMS-TChiHH_unsplit/SMS-TChiHH_*_TuneCP2_13TeV-madgraphMLM-pythia8__RunIIAutumn18NanoAODv5__PUFall18Fast_Nano1June2019_102X_upgrade2018_realistic_v19-v1_*.root" -o /net/cms29/cms29r0/pico/NanoAODv5/nano/2018/SMS-TChiHH_2D/"'
job_log_string = queue_system.decompress_string(sys.argv[1])
job_argument_string = queue_system.decompress_string(sys.argv[2])

print(job_argument_string)

#argDict = argument_string_to_dict(job_argument_string)

args = job_argument_string.split('--command="')[1].split('"')[0]
tmp = args.split(' ')
#print(tmp)
infile_path = tmp[4]
lsp_mass = 0
if (tmp[1]=='-m'):
  #higgsino splitting job, have to deal with extra wildcard *'s and thus "s
  pre_args = job_argument_string.split('--command="')[1].split('"')
  args = pre_args[0]+pre_args[1]+pre_args[2]
  tmp = args.split(' ')
  if (tmp[3]!='-l'):
    infile_path = tmp[4]
  else:
    #2d scan
    infile_path = tmp[6]
    lsp_mass = int(tmp[4])

if '/merged_' in infile_path or '/raw_pico_' in infile_path: 
  in_dir = os.path.dirname(infile_path)
  skim_name = tmp[2]
  out_dir = tmp[6]
  outfile_path = infile_path.replace(in_dir,out_dir).replace('pico_','pico_'+skim_name+'_')
elif tmp[1]=='-m':
  #higgsino splitting job
  if (tmp[3]!='-l'):
    out_filename = tmp[4]
    out_filename = (os.path.basename(out_filename)).replace('_*','')
    out_filename = out_filename.replace('SMS-TChiHH', 'SMS-TChiHH_mChi-'+str(tmp[2])+'_mLSP-0')
    outfile_path = os.path.join(tmp[6], out_filename)
  else:
    #2d scan
    out_filename = tmp[6]
    out_filename = (os.path.basename(out_filename)).replace('_*','')
    out_filename = out_filename.replace('SMS-TChiHH', 'SMS-TChiHH_mChi-'+str(tmp[2])+'_mLSP-'+str(tmp[4]))
    outfile_path = os.path.join(tmp[8], out_filename)
else:
  outfile_basename = tmp[4].split('/')[-1][5:]
  outfile_path = tmp[6]+'pico_'+tmp[2]+'_'+outfile_basename


if tmp[1]=='-m':
  infile = TChain("Events");
  infile.Add(infile_path);
  cut_string = "(MaxIf$(GenPart_mass,GenPart_pdgId==1000023)>"+str(int(tmp[2])-10)+"&&MaxIf$(GenPart_mass,GenPart_pdgId==1000023)<"+str(int(tmp[2])+10)+")"
  cut_string += "&&(MaxIf$(GenPart_mass,GenPart_pdgId==1000022)>"+str(lsp_mass-10)+"&&MaxIf$(GenPart_mass,GenPart_pdgId==1000022)<"+str(lsp_mass+10)+")"
  in_nent = infile.GetEntries(cut_string)
  if os.path.exists(outfile_path):
    outfile = TChain("Events");
    outfile.Add(outfile_path);
    out_nent = outfile.GetEntries()
  else:
    out_nent = 0
  if outfile.GetNbranches() == 0:
    print('[For queue_system] fail: output ({}) has no branches.'.format(outfile_path))
  elif in_nent == out_nent:
    print('[For queue_system] success')
  else:
    print('[For queue_system] fail: Input ({}) has {} entries, while output ({}) has {} entries.'.format(infile_path, in_nent, outfile_path, out_nent))
else: 
  infile = TChain("tree");
  infile.Add(infile_path);
  in_nent = infile.GetEntries(get_cuts(tmp[2]))
  if os.path.exists(outfile_path):
    outfile = TChain("tree");
    outfile.Add(outfile_path);
    out_nent = outfile.GetEntries()
    nbranches = outfile.GetNbranches()
  else:
    out_nent = 0
    nbranches = 0
  if os.path.exists(outfile_path) and nbranches == 0:
    print('[For queue_system] fail: output ({}) has no branches.'.format(outfile_path))
  elif in_nent == out_nent:
    print('[For queue_system] success')
  else:
    print('[For queue_system] fail: Input ({}) has {} entries, while output ({}) has {} entries.'.format(infile_path, in_nent, outfile_path, out_nent))
