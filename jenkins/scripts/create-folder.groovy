// Import necessary classes
import jenkins.model.*
import com.cloudbees.hudson.plugins.folder.Folder

def jenkins = Jenkins.getInstance()

// Create the ai-dev-agent folder if it doesn't exist
if (jenkins.getItem("ai-dev-agent") == null) {
    println "Creating ai-dev-agent folder"
    jenkins.createProject(Folder.class, "ai-dev-agent")
    println "Folder created successfully"
}
