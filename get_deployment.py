#!/usr/local/python3/bin/python3.6
import yaml
import json
import os
import time
import sys
import xlwt
import xlrd
from xlutils.copy import copy as xl_copy

item=sys.argv[1]
timer = round(time.time() * 1000)

cluster={'蛮牛':'ca81c0f112fc84e21bbc0024963402bf7','商城':'c8056aee7263b451bbeaee667d7b57288'}
depurl=f"https://cs.console.aliyun.com/apiProxy/mirana/region/{cluster[item]}/apis/apps/v1/deployments?__preventCache={timer}"
usageurl=f"https://cs.console.aliyun.com/apiProxy/mirana/cn-shanghai/{cluster[item]}/apis/metrics.k8s.io/v1beta1/pods?__preventCache={timer}"
hpaurl=f"https://cs.console.aliyun.com/apiProxy/mirana/region/{cluster[item]}/apis/autoscaling/v1/horizontalpodautoscalers?__preventCache={timer}"
stsurl=f"https://cs.console.aliyun.com/apiProxy/mirana/region/{cluster[item]}/apis/apps/v1/statefulsets?__preventCache={timer}"
os.environ['depurl'] = str(depurl)
os.environ['usageurl'] = str(usageurl)
os.environ['hpaurl'] = str(hpaurl)
os.environ['stsurl'] = str(stsurl)
os.system('rm -rf /tmp/*.json')
os.system('wget -q  -t 0 --load-cookies /root/cookies.txt $depurl -O  /tmp/req.json')
os.system('wget -q  -t 0 --load-cookies /root/cookies.txt $usageurl -O  /tmp/podusage.json')
os.system('wget -q  -t 0 --load-cookies /root/cookies.txt $hpaurl -O  /tmp/hpa.json')
os.system('wget -q  -t 0 --load-cookies /root/cookies.txt $stsurl -O  /tmp/sts.json')

def hpa():
    with open(f"/tmp/hpa.json",'r') as f3:
         hpa_data = json.load(f3)
         hpa=hpa_data['data']['items']
         hpa_list=[]
         for h in range(len(hpa)):
             minrep=hpa[h]['spec']['minReplicas']
             maxrep=hpa[h]['spec']['maxReplicas']
             currep=hpa[h]['status']['currentReplicas']
             ns=hpa[h]['metadata']['namespace']
             if ns == "kube-system":
                continue
             elif ns == "arms-pilot":
                continue
             elif ns == "arms-prom":
                continue
             elif ns == "catalog":
                continue
             app=hpa[h]['metadata']['name']
             dhpa=dict(name=app,ns=ns,minrep=minrep,maxrep=maxrep,currep=currep)
             hpa_list.append(dhpa)
         return hpa_list

def sts():
    with open(f"/tmp/sts.json",'r') as f4:
         sts_data = json.load(f4)
         sts=sts_data['data']['items']
         sts_list=[]
         for stsreq in range(len(sts)):
             name=sts[stsreq]['metadata']['name']
             ns=sts[stsreq]['metadata']['namespace']
             if ns == "kube-system":
                continue
             elif ns == "arms-pilot":
                continue
             elif ns == "arms-prom":
                continue
             resources=sts[stsreq]['spec']['template']['spec']['containers'][0].get('resources','no resources')
             if resources != 'no resources':
                requests=resources.get('requests','no requests')
                if requests != 'no requests':
                   requests['name']=name
                   requests['ns']=ns
                   requests['cpu_req']=requests['cpu']
                   requests['mem_req']=requests['memory']
                   requests.pop('cpu')
                   requests.pop('memory')
                   sts_list.append(requests)
                else:
                   requests=dict(name=name,ns=ns,cpu_req='',mem_req='')
                   sts_list.append(requests)
             else:
                requests=dict(name=name,ns=ns,cpu_req='',mem_req='')
                sts_list.append(requests)
         return sts_list 
        
def pod_usage():
    with open(f"/tmp/podusage.json",'r') as f:
         dict_data = json.load(f)
         data=dict_data['data']
         new_data=data['items']
         all_list=pod_req()
         poduse_list=[]
         for p in range(len(new_data)):
             usage=new_data[p]['containers'][0]['usage']
             cpu=usage['cpu']
             mem=usage['memory']
             if 'Ki' in mem:
                Mem=mem.replace('Ki','') 
                MEM=str(round(int(Mem)/1024/1024,3))+'Gi'
             pod=new_data[p]['metadata']['name']
             ns=new_data[p]['metadata']['namespace']
             name=new_data[p]['containers'][0]['name']
             if ns == "kube-system":
                continue
             elif ns == "arms-pilot":
                continue
             elif ns == "arms-prom":
                continue
             usage=dict(ns=ns,name=name,pod=pod,cpu=cpu,mem=MEM)
             for m in range(len(all_list)):
                 if all_list[m]['name'] == usage['name'] and all_list[m]['ns'] == usage['ns']:
                    usage.update(all_list[m])
                    poduse_list.append(usage)
                 elif all_list[m]['ns'] == 'zookeeper' and usage['ns'] == 'zookeeper':
                    usage.update(all_list[m])
                    poduse_list.append(usage)
         return poduse_list

def pod_req():
    with open(f"/tmp/req.json",'r') as f1:
         dict_data = json.load(f1)
         data=dict_data['data']
         new_data=data['items']
         pod_list=[]
         sts_list=sts()
         for i in range(len(new_data)):
             ns=new_data[i]['metadata']['namespace']
             if ns == "kube-system":
                continue
             elif ns == "arms-pilot":
                continue
             elif ns == "arms-prom":
                continue
             elif ns == "catalog":
                continue
             replicas=new_data[i]['status'].get('availableReplicas','no rep')
             if replicas == 'no rep':  #过滤副本数0的应用
                continue
             container=new_data[i]['spec']['template']['spec']['containers'][0]
             appname=container['name']
             resource=container.get('resources','no resources')

             requests=''
             if resource != 'no resources':
                requests=resource.get('requests','no requests')
                if requests != 'no requests':
                   vol=requests.get('ephemeral-storage','no vol')
                   if vol != 'no vol':
                      requests.pop('ephemeral-storage')
                   requests['name']=appname
                   requests['ns']=ns
                   requests['cpu_req']=requests['cpu']
                   requests['mem_req']=requests['memory']
                   requests.pop('cpu')
                   requests.pop('memory')
                   pod_list.append(requests)
                else:
                   requests=dict(name=appname,ns=ns,cpu_req='',mem_req='')
                   pod_list.append(requests)
             else:
                requests=dict(name=appname,ns=ns,cpu_req='',mem_req='')
                pod_list.append(requests)
         all_list=pod_list+sts_list  #sts+deployment
         return all_list 

def createexcel():
    workbook=xlwt.Workbook(encoding='utf-8')
    worksheet=workbook.add_sheet(f"资源使用情况")
    usageamount=pod_usage()
    usageamount.insert(0,dict(ns='命名空间',name='应用名',pod='pod名',cpu_req='cpu请求',cpu='cpu使用',mem_req='mem请求',mem='mem使用'))
    for per in range(len(usageamount)):
        worksheet.write(per,0,usageamount[per]['ns'])   
        worksheet.write(per,1,usageamount[per]['name'])   
        worksheet.write(per,2,usageamount[per]['pod'])   
        worksheet.write(per,3,usageamount[per]['cpu_req'])   
        worksheet.write(per,4,usageamount[per]['cpu'])   
        worksheet.write(per,5,usageamount[per]['mem_req'])   
        worksheet.write(per,6,usageamount[per]['mem'])   
    worksheet.set_panes_frozen(True) #设置冻结窗口
    worksheet.set_horz_split_pos(1)
    
    Sheet1=workbook.add_sheet('HPA')
    hpa_data=hpa()
    hpa_data.insert(0,dict(ns='命名空间',name='应用名',minrep='最小副本数',maxrep='最大副本数',currep='当前副本数'))
    for a in range(len(hpa_data)):
        Sheet1.write(a,0,hpa_data[a]['ns'])
        Sheet1.write(a,1,hpa_data[a]['name'])
        Sheet1.write(a,2,hpa_data[a]['minrep'])
        Sheet1.write(a,3,hpa_data[a]['maxrep'])
        Sheet1.write(a,4,hpa_data[a]['currep'])
    Sheet1.set_panes_frozen(True) #设置冻结窗口
    Sheet1.set_horz_split_pos(1)
    workbook.save(f"/data/{item}pod数及资源使用情况.xlsx")
    
createexcel()
