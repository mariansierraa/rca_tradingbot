' Copyright (C) 2023 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
' and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.

Imports System
Imports System.Collections.Generic
Imports System.Linq
Imports System.Text
Imports System.Threading.Tasks

Namespace Samples

    Public Class FaAllocationSamples

        '! [faupdatedgroup]
        'Replace with your own accountIds
        Public Shared FaUpdatedGroup As String = "<?xml version=""1.0"" encoding=""UTF-8""?>" &
            "<ListOfGroups>" &
                "<Group>" &
                    "<name>MyTestProfile1</name>" &
                    "<defaultMethod>ContractsOrShares</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                            "<amount>100.0</amount>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                            "<amount>200.0</amount>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>MyTestProfile2</name>" &
                    "<defaultMethod>Ratio</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                            "<amount>1.0</amount>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                            "<amount>2.0</amount>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>MyTestProfile3</name>" &
                    "<defaultMethod>Percent</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                            "<amount>60.0</amount>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                            "<amount>40.0</amount>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                "<name>MyTestProfile4</name>" &
                    "<defaultMethod>MonetaryAmount</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                            "<amount>1000.0</amount>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                            "<amount>2000.0</amount>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>Group_1</name>" &
                    "<defaultMethod>NetLiq</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>MyTestGroup1</name>" &
                    "<defaultMethod>AvailableEquity</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>MyTestGroup2</name>" &
                    "<defaultMethod>NetLiq</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>MyTestGroup3</name>" &
                    "<defaultMethod>Equal</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
                "<Group>" &
                    "<name>Group_2</name>" &
                    "<defaultMethod>AvailableEquity</defaultMethod>" &
                    "<ListOfAccts varName=""list"">" &
                        "<Account>" &
                            "<acct>DU6202167</acct>" &
                        "</Account>" &
                        "<Account>" &
                            "<acct>DU6202168</acct>" &
                        "</Account>" &
                    "</ListOfAccts>" &
                "</Group>" &
            "</ListOfGroups>"
        '! [faupdatedgroup]
    End Class
End Namespace

