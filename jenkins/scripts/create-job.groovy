// Import necessary classes
import jenkins.model.*
import hudson.model.*
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition
import hudson.plugins.git.GitSCM
import hudson.plugins.git.BranchSpec
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import com.cloudbees.hudson.plugins.folder.Folder

def jenkins = Jenkins.getInstance()

// Create a folder for the AI dev agent project
def projectFolder = jenkins.getItem("ai-dev-agent")
if (projectFolder == null) {
    projectFolder = jenkins.createProject(Folder.class, "ai-dev-agent")
    println "Created folder: ai-dev-agent"
}

// Read the Jenkinsfile template
def templateFile = new File("/var/jenkins_home/jobTemplates/Jenkinsfile.template")
if (templateFile.exists()) {
    def jenkinsfileContent = templateFile.text

    // Create the pipeline job
    def pipelineJob = projectFolder.getItem("main-pipeline")
    if (pipelineJob == null) {
        pipelineJob = projectFolder.createProject(WorkflowJob.class, "main-pipeline")
    }
    
    // Set pipeline definition directly from the template
    pipelineJob.setDefinition(new CpsFlowDefinition(jenkinsfileContent, true))
    
    // Save the job configuration
    pipelineJob.save()
    
    println "AI Dev Agent pipeline job created successfully"
} else {
    println "Jenkinsfile template not found"
}
